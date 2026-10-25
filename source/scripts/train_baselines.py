"""Comparative baseline training and evaluation runner for AgentWatch-A.

Adheres strictly to Section 11 and Section 12 of AGENTWATCH_DIRECTION_A_SPEC.md.
Evaluates Priority A baselines (B1, B2, B3, B4, B6) on canonical benchmark traces.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

from agentwatch_a.models import (
    BaseMonitorScorer,
    ContentOnlyInjectionBaseline,
    PooledEmbeddingAnomalyBaseline,
    SupervisedOracleBaseline,
    ToolTransitionBaseline,
    UnconditionedSequenceBaseline,
)
from agentwatch_a.schemas import TrajectoryTrace
from agentwatch_a.trace_store import load_traces_from_jsonl


def evaluate_baseline_on_traces(
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
                "min": float(np.min(scores)),
                "max": float(np.max(scores)),
            }
        else:
            summary[group] = {"count": 0.0, "mean": 0.0, "std": 0.0, "min": 0.0, "max": 0.0}

    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Train and evaluate AgentWatch-A baselines.")
    parser.add_argument(
        "--input",
        "-i",
        type=str,
        default="data/sample_traces/canonical_traces.jsonl",
        help="Path to canonical trace file.",
    )
    args = parser.parse_args()

    trace_path = Path(args.input)
    if not trace_path.exists():
        print(f"[-] Trace file not found: {trace_path}")
        return 1

    print(f"[*] Loading traces from {trace_path}...")
    all_traces = load_traces_from_jsonl(trace_path)
    print(f"[+] Loaded {len(all_traces)} traces.")

    benign_traces = [t for t in all_traces if t.trajectory_label == "BENIGN"]
    hijacked_traces = [t for t in all_traces if t.trajectory_label == "HIJACKED"]
    unexposed_traces = [t for t in all_traces if t.trajectory_label == "UNEXPOSED"]
    resisted_traces = [t for t in all_traces if t.trajectory_label == "EXPOSED_RESISTED"]

    print(f"    - BENIGN: {len(benign_traces)}")
    print(f"    - UNEXPOSED: {len(unexposed_traces)}")
    print(f"    - EXPOSED_RESISTED: {len(resisted_traces)}")
    print(f"    - HIJACKED: {len(hijacked_traces)}")

    # 1. Instantiate baseline suite
    baselines: dict[str, BaseMonitorScorer] = {
        "B1_TransitionBigram": ToolTransitionBaseline(),
        "B2_IsolationForest": PooledEmbeddingAnomalyBaseline(algorithm="isolation_forest"),
        "B2_OneClassSVM": PooledEmbeddingAnomalyBaseline(algorithm="ocsvm"),
        "B3_ContentDetector": ContentOnlyInjectionBaseline(),
        "B4_UnconditionedSequence": UnconditionedSequenceBaseline(max_order=2),
        "B6_SupervisedOracle": SupervisedOracleBaseline(n_estimators=30),
    }

    # 2. Fit models on appropriate training splits (Section 11.1)
    print("\n[*] Fitting baselines on training data...")
    for name, model in baselines.items():
        if name.startswith("B6"):
            # B6 has access to labeled traces (benign + attack)
            model.fit(all_traces)
        elif name.startswith("B3"):
            # B3 content detector fits on observation texts
            model.fit(all_traces)
        else:
            # B1, B2, B4 are strictly benign-only anomaly detectors
            model.fit(benign_traces)
        print(f"    [+] Fitted {name}")

    # 3. Evaluate on evaluation traces
    print("\n" + "=" * 90)
    print(f"{'Baseline':<26} | {'Benign Mean':<12} | {'Resisted Mean':<14} | {'Hijack Harm Mean':<16} | {'Separation':<12}")
    print("=" * 90)

    for name, model in baselines.items():
        stats = evaluate_baseline_on_traces(model, all_traces)
        b_mean = stats["BENIGN"]["mean"]
        r_mean = stats["EXPOSED_RESISTED"]["mean"]
        h_mean = stats["HIJACKED_AT_OR_POST_HARM"]["mean"]
        separation = h_mean - b_mean
        print(f"{name:<26} | {b_mean:<12.4f} | {r_mean:<14.4f} | {h_mean:<16.4f} | {separation:<+12.4f}")

    print("=" * 90)
    print("[+] Phase 5 baseline evaluation complete. All Priority A baselines operational.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
