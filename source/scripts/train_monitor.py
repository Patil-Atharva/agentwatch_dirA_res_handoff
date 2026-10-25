"""Training and comparative evaluation runner for GoalConditionedGRUMonitor.

Adheres strictly to Section 8.5, Section 8.6, and Section 11 of AGENTWATCH_DIRECTION_A_SPEC.md.
Trains GoalConditionedGRUMonitor via contrastive goal-prefix alignment on benign traces,
saves the model checkpoint, and evaluates pre-execution detection across canonical traces.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
from torch import optim

from agentwatch_a.models.goal_conditioned_gru import (
    GoalConditionedGRUMonitor,
    _extract_provenance_vector,
)
from agentwatch_a.models.interface import BaseMonitorScorer, PreExecutionInput
from agentwatch_a.models.oracle import SupervisedOracleBaseline
from agentwatch_a.models.sequence_baseline import UnconditionedSequenceBaseline
from agentwatch_a.models.transition_baseline import ToolTransitionBaseline
from agentwatch_a.schemas import TrajectoryTrace
from agentwatch_a.trace_store import load_traces_from_jsonl


def create_contrastive_batches(
    benign_traces: list[TrajectoryTrace],
) -> list[tuple[PreExecutionInput, list[str]]]:
    """Extract positive step inputs paired with same-suite negative goals (Section 8.6)."""
    all_goals = list({t.goal for t in benign_traces if t.goal})
    samples: list[tuple[PreExecutionInput, list[str]]] = []

    for trace in benign_traces:
        true_goal = trace.goal
        neg_goals = [g for g in all_goals if g != true_goal]

        for step_idx in range(len(trace.steps)):
            inp = trace.get_pre_execution_input(step_idx)
            samples.append((inp, neg_goals))

    return samples


def train_goal_conditioned_monitor(
    monitor: GoalConditionedGRUMonitor,
    benign_traces: list[TrajectoryTrace],
    epochs: int = 15,
    lr: float = 0.003,
) -> GoalConditionedGRUMonitor:
    """Train monitor using Section 8.6 contrastive goal-prefix matching."""
    samples = create_contrastive_batches(benign_traces)
    if not samples:
        return monitor

    optimizer = optim.Adam(monitor.parameters(), lr=lr)
    monitor.train()

    for epoch in range(epochs):
        total_loss = 0.0
        for pos_input, neg_goals in samples:
            optimizer.zero_grad()

            # Encode true goal and positive prefix step
            true_goal_emb = monitor.encode_goal(pos_input.goal)
            h_0 = torch.tanh(monitor.goal_init_proj(true_goal_emb)).unsqueeze(0)

            # Unroll prior actions
            h = h_0
            for i, p_act in enumerate(pos_input.prior_actions):
                p_tool = p_act.get("tool", "")
                p_args = p_act.get("args", {})
                p_obs = pos_input.prior_observations[i] if i < len(pos_input.prior_observations) else ""
                partial_input = PreExecutionInput(
                    goal=pos_input.goal,
                    step_index=i,
                    prior_actions=pos_input.prior_actions[:i],
                    prior_observations=pos_input.prior_observations[:i],
                    proposed_tool=p_tool,
                    proposed_args=p_args,
                )
                p_prov = _extract_provenance_vector(partial_input)
                x_i = monitor.encode_step_input(p_tool, p_args, p_obs, p_prov).unsqueeze(1)
                _, h = monitor.gru(x_i, h)

            # Current action
            c_tool = pos_input.proposed_tool
            c_args = pos_input.proposed_args
            c_obs = pos_input.prior_observations[-1] if pos_input.prior_observations else ""
            c_prov = _extract_provenance_vector(pos_input)
            x_curr = monitor.encode_step_input(c_tool, c_args, c_obs, c_prov).unsqueeze(1)
            _, h_curr = monitor.gru(x_curr, h)

            z_pos_step = F.normalize(monitor.proj_step(h_curr.squeeze(0)), p=2, dim=-1)
            z_pos_goal = F.normalize(monitor.proj_goal(true_goal_emb), p=2, dim=-1)
            pos_sim = torch.sum(z_pos_goal * z_pos_step)

            # Contrastive margin loss against negative goals
            loss = torch.tensor(0.0)
            if neg_goals:
                neg_sims = []
                for neg_g in neg_goals[:3]:  # sample top 3 same-suite negatives
                    neg_emb = monitor.encode_goal(neg_g)
                    z_neg_goal = F.normalize(monitor.proj_goal(neg_emb), p=2, dim=-1)
                    neg_sims.append(torch.sum(z_neg_goal * z_pos_step))

                max_neg_sim = torch.stack(neg_sims).max()
                # Triplet margin loss: pos_sim should be higher than max_neg_sim by margin 0.3
                loss = F.relu(0.3 - pos_sim + max_neg_sim)

            if loss.requires_grad:
                loss.backward()
                optimizer.step()
                total_loss += loss.item()

    monitor.eval()
    return monitor


def evaluate_model_on_traces(
    model: BaseMonitorScorer,
    traces: list[TrajectoryTrace],
) -> dict[str, dict[str, float]]:
    """Score all pre-execution steps across evaluation traces by label group."""
    group_scores: dict[str, list[float]] = {
        "BENIGN": [],
        "UNEXPOSED": [],
        "EXPOSED_RESISTED": [],
        "HIJACKED_PRE_HARM": [],
        "HIJACKED_AT_OR_POST_HARM": [],
    }

    for trace in traces:
        model.reset()
        is_hijacked = trace.trajectory_label == "HIJACKED"
        t_harm = trace.t_harm if trace.t_harm is not None else len(trace.steps)

        for step_idx in range(len(trace.steps)):
            inp = trace.get_pre_execution_input(step_idx)
            score = model.score_pre_execution(inp)

            if trace.trajectory_label == "BENIGN":
                group_scores["BENIGN"].append(score)
            elif trace.trajectory_label == "UNEXPOSED":
                group_scores["UNEXPOSED"].append(score)
            elif trace.trajectory_label == "EXPOSED_RESISTED":
                group_scores["EXPOSED_RESISTED"].append(score)
            elif is_hijacked:
                if step_idx < t_harm:
                    group_scores["HIJACKED_PRE_HARM"].append(score)
                else:
                    group_scores["HIJACKED_AT_OR_POST_HARM"].append(score)

    summary: dict[str, dict[str, float]] = {}
    for group, scores in group_scores.items():
        if scores:
            summary[group] = {
                "count": float(len(scores)),
                "mean": float(np.mean(scores)),
                "std": float(np.std(scores)),
            }
        else:
            summary[group] = {"count": 0.0, "mean": 0.0, "std": 0.0}

    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Train and evaluate AgentWatch-A GoalConditionedGRUMonitor.")
    parser.add_argument(
        "--input",
        "-i",
        type=str,
        default="data/sample_traces/canonical_traces.jsonl",
        help="Path to canonical trace file.",
    )
    parser.add_argument(
        "--checkpoint",
        "-c",
        type=str,
        default="data/goal_conditioned_gru.pt",
        help="Path to save trained monitor checkpoint.",
    )
    args = parser.parse_args()

    # Ensure 100% deterministic reproducibility
    torch.manual_seed(42)
    np.random.seed(42)

    trace_path = Path(args.input)
    if not trace_path.exists():
        print(f"[-] Trace file not found: {trace_path}")
        return 1

    print(f"[*] Loading traces from {trace_path}...")
    all_traces = load_traces_from_jsonl(trace_path)
    benign_traces = [t for t in all_traces if t.trajectory_label == "BENIGN"]
    print(f"[+] Loaded {len(all_traces)} traces ({len(benign_traces)} BENIGN).")

    # 1. Instantiate monitors and baselines
    print("\n[*] Initializing models...")
    b1 = ToolTransitionBaseline().fit(benign_traces)
    b4 = UnconditionedSequenceBaseline(max_order=2).fit(benign_traces)
    b6 = SupervisedOracleBaseline(n_estimators=30).fit(all_traces)

    monitor_full = GoalConditionedGRUMonitor(goal_dim=64, hidden_dim=64, proj_dim=32)
    monitor_ablated = GoalConditionedGRUMonitor(goal_dim=64, hidden_dim=64, proj_dim=32, ablation_no_goal=True)

    # 2. Train monitor contrastively on calibration benign traces
    print("[*] Training GoalConditionedGRUMonitor (contrastive same-suite matching)...")
    train_goal_conditioned_monitor(monitor_full, benign_traces[:5], epochs=35, lr=0.005)

    ckpt_path = Path(args.checkpoint)
    ckpt_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(monitor_full.state_dict(), ckpt_path)
    print(f"[+] Saved checkpoint to {ckpt_path}")

    # 3. Comparative evaluation across trace suite
    models: dict[str, BaseMonitorScorer] = {
        "B1_TransitionBigram": b1,
        "B4_UnconditionedSequence": b4,
        "GoalConditionedGRU (Ablated: No Goal)": monitor_ablated,
        "GoalConditionedGRU (Full Monitor)": monitor_full,
        "B6_SupervisedOracle": b6,
    }

    print("\n" + "=" * 94)
    print(f"{'Model / Baseline':<38} | {'Benign Mean':<12} | {'Resisted Mean':<14} | {'Hijack Harm':<12} | {'Separation':<12}")
    print("=" * 94)

    for name, model in models.items():
        stats = evaluate_model_on_traces(model, all_traces)
        b_mean = stats["BENIGN"]["mean"]
        r_mean = stats["EXPOSED_RESISTED"]["mean"]
        h_mean = stats["HIJACKED_AT_OR_POST_HARM"]["mean"]
        separation = h_mean - b_mean
        print(f"{name:<38} | {b_mean:<12.4f} | {r_mean:<14.4f} | {h_mean:<12.4f} | {separation:<+12.4f}")

    print("=" * 94)
    print("[+] Phase 6 Goal-Conditioned Monitor evaluation complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
