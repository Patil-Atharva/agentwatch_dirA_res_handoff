"""Evaluation metrics, statistical analysis, and ablations for AgentWatch-A."""

from agentwatch_a.evaluation.metrics import (
    EvaluationMetricsReport,
    TrajectoryEvaluation,
    compute_metrics_suite,
    evaluate_trajectory_detection,
)

__all__ = [
    "EvaluationMetricsReport",
    "TrajectoryEvaluation",
    "compute_metrics_suite",
    "evaluate_trajectory_detection",
]
