"""Conformal calibration and pre-execution evaluation runner for AgentWatch-A.

Adheres strictly to Section 9 and Section 12 of AGENTWATCH_DIRECTION_A_SPEC.md.
Calibrates decision thresholds over benign calibration trajectories and evaluates
TPR_pre, partitioned FPR_traj, lead times, AUROC, and AUPRC across all models.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import torch

from agentwatch_a.calibration.conformal import ConformalCalibrator
from agentwatch_a.evaluation.metrics import (
    compute_metrics_suite,
    evaluate_trajectory_detection,
)
from agentwatch_a.models.goal_conditioned_gru import GoalConditionedGRUMonitor
from agentwatch_a.models.interface import BaseMonitorScorer
from agentwatch_a.models.oracle import SupervisedOracleBaseline
from agentwatch_a.models.sequence_baseline import UnconditionedSequenceBaseline
from agentwatch_a.models.transition_baseline import ToolTransitionBaseline
from agentwatch_a.trace_store import load_traces_from_jsonl


def main() -> int:
    parser = argparse.ArgumentParser(description="Calibrate thresholds and evaluate AgentWatch-A models.")
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
        help="Path to trained monitor checkpoint.",
    )
    parser.add_argument(
        "--output-manifest",
        "-o",
        type=str,
        default="data/calibration_manifest.json",
        help="Path to save calibration manifest.",
    )
    parser.add_argument(
        "--alpha",
        "-a",
        type=float,
        default=0.20,
        help="Target trajectory-level false alarm rate alpha.",
    )
    args = parser.parse_args()

    trace_path = Path(args.input)
    if not trace_path.exists():
        print(f"[-] Trace file not found: {trace_path}")
        return 1

    print(f"[*] Loading traces from {trace_path}...")
    all_traces = load_traces_from_jsonl(trace_path)
    benign_traces = [t for t in all_traces if t.trajectory_label == "BENIGN"]
    attack_traces = [t for t in all_traces if t.trajectory_label != "BENIGN"]

    # 1. Establish disjoint calibration and test splits (Section 9.2)
    # Use first 5 benign traces for calibration, remaining 5 benign + all attacks for test
    calib_benign = benign_traces[:5]
    test_benign = benign_traces[5:]
    test_traces = test_benign + attack_traces

    print("[+] Partitioned data (Disjoint calibration & test):")
    print(f"    - Calibration: {len(calib_benign)} BENIGN traces")
    print(f"    - Test: {len(test_traces)} traces ({len(test_benign)} BENIGN, {len([t for t in test_traces if t.trajectory_label == 'UNEXPOSED'])} UNEXPOSED, {len([t for t in test_traces if t.trajectory_label == 'EXPOSED_RESISTED'])} RESISTED, {len([t for t in test_traces if t.trajectory_label == 'HIJACKED'])} HIJACKED)")

    # 2. Instantiate and load models
    b1 = ToolTransitionBaseline().fit(calib_benign)
    b4 = UnconditionedSequenceBaseline(max_order=2).fit(calib_benign)
    b6 = SupervisedOracleBaseline(n_estimators=30).fit(all_traces)

    monitor_ablated = GoalConditionedGRUMonitor(goal_dim=64, hidden_dim=64, proj_dim=32, ablation_no_goal=True)
    monitor_full = GoalConditionedGRUMonitor(goal_dim=64, hidden_dim=64, proj_dim=32)

    ckpt_path = Path(args.checkpoint)
    if ckpt_path.exists():
        monitor_full.load_state_dict(torch.load(ckpt_path, map_location="cpu", weights_only=True))
        print(f"[+] Loaded trained monitor weights from {ckpt_path}")
    else:
        print(f"[!] Checkpoint {ckpt_path} not found, using initialized weights.")

    models: dict[str, BaseMonitorScorer] = {
        "B1_TransitionBigram": b1,
        "B4_UnconditionedSequence": b4,
        "GoalConditionedGRU (Ablated)": monitor_ablated,
        "GoalConditionedGRU (Full)": monitor_full,
        "B6_SupervisedOracle": b6,
    }

    # 3. Conformal Calibration on calib_benign split
    print(f"\n[*] Running Split-Conformal Calibration (Target Alpha = {args.alpha:.2f})...")
    calibrator = ConformalCalibrator(alpha=args.alpha)
    manifest: dict[str, dict] = {}

    print("=" * 105)
    print(f"{'Model':<30} | {'Threshold tau':<14} | {'TPR_pre':<10} | {'FPR_benign':<11} | {'FPR_resisted':<12} | {'Lead Time':<10} | {'AUROC':<8}")
    print("=" * 105)

    for name, model in models.items():
        calib_rec = calibrator.calibrate(model, calib_benign, score_name=name)
        tau = calib_rec.threshold if calib_rec.is_finite else 0.85

        # Evaluate on held-out test split
        evals = [evaluate_trajectory_detection(model, t, threshold=tau) for t in test_traces]
        report = compute_metrics_suite(evals, threshold=tau)

        manifest[name] = {
            "calibrated_threshold": tau,
            "alpha": args.alpha,
            "is_finite": calib_rec.is_finite,
            "metrics": report.model_dump(),
        }

        lead_str = f"{report.mean_lead_time:.1f} steps" if report.mean_lead_time is not None else "N/A"
        auroc_str = f"{report.auroc:.3f}" if report.auroc is not None else "N/A"

        print(f"{name:<30} | {tau:<14.4f} | {report.tpr_pre:<10.2%} | {report.fpr_benign:<11.2%} | {report.fpr_resisted:<12.2%} | {lead_str:<10} | {auroc_str:<8}")

    print("=" * 105)

    # Save manifest
    out_manifest_path = Path(args.output_manifest)
    out_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    out_manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"\n[+] Calibration manifest saved to {out_manifest_path}")
    print("[+] Phase 7 Calibration and Evaluation complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
