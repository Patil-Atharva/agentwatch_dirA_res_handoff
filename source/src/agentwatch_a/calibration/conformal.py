"""Split-conformal calibration on trajectory-level maximum risk scores.

Adheres strictly to Section 9 of AGENTWATCH_DIRECTION_A_SPEC.md.
Calibrates pre-execution threshold tau targeting marginal trajectory-level
false positive rate control (FPR_traj <= alpha).
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

from agentwatch_a.models.interface import BaseMonitorScorer

if TYPE_CHECKING:
    from agentwatch_a.schemas import TrajectoryTrace


class CalibratedThresholdRecord(BaseModel):
    """Immutable record of a calibrated conformal decision threshold."""
    model_config = ConfigDict(extra="forbid")

    alpha: float = Field(ge=0.0, le=1.0, description="Target trajectory-level false alarm rate.")
    sample_count: int = Field(ge=0, description="Number of benign calibration units.")
    k_order_statistic: int = Field(ge=1, description="Target order statistic index k = ceil((n+1)(1-alpha)).")
    threshold: float = Field(description="Calibrated decision threshold (or inf if k = n+1).")
    is_finite: bool = Field(description="Whether the threshold is finite.")
    score_definition: str = Field(description="Description of the calibrated scoring function.")
    calibration_run_ids: list[str] = Field(default_factory=list, description="IDs of calibration trajectories.")


def compute_conformal_order_statistic(n: int, alpha: float) -> int:
    """Compute conservative conformal order statistic index k = ceil((n + 1) * (1 - alpha))."""
    if n <= 0:
        raise ValueError("Calibration sample size n must be positive.")
    if not (0.0 < alpha < 1.0):
        raise ValueError("Target alpha must be strictly in (0, 1).")
    return math.ceil((n + 1) * (1.0 - alpha))


def compute_conformal_threshold(
    max_scores: Sequence[float],
    alpha: float = 0.05,
) -> tuple[float, int, bool]:
    """Compute conservative split-conformal threshold from calibration maximum scores.

    Returns:
        (threshold, k, is_finite)
    """
    n = len(max_scores)
    k = compute_conformal_order_statistic(n, alpha)

    if k > n:
        # Section 9.3: If k = n + 1, return infinite threshold
        return float("inf"), k, False

    sorted_scores = sorted(max_scores)
    # k is 1-indexed; in 0-indexed Python array, take sorted_scores[k - 1]
    tau = float(sorted_scores[k - 1])
    return tau, k, True


class ConformalCalibrator:
    """Calibrates monitor decision threshold over benign calibration trajectories."""

    def __init__(self, alpha: float = 0.05):
        self.alpha = alpha

    def calibrate(
        self,
        scorer: BaseMonitorScorer,
        calibration_traces: Sequence[TrajectoryTrace],
        score_name: str = "max_prefix_risk",
    ) -> CalibratedThresholdRecord:
        """Run frozen monitor over benign calibration trajectories and extract conformal threshold."""
        benign_traces = [t for t in calibration_traces if t.trajectory_label == "BENIGN"]
        if not benign_traces:
            raise ValueError("Calibration requires at least one BENIGN trajectory.")

        max_scores: list[float] = []
        run_ids: list[str] = []

        for trace in benign_traces:
            scorer.reset()
            step_scores: list[float] = []
            for step_idx in range(len(trace.steps)):
                inp = trace.get_pre_execution_input(step_idx)
                s = scorer.score_pre_execution(inp)
                step_scores.append(s)

            m_i = max(step_scores) if step_scores else 0.0
            max_scores.append(m_i)
            run_ids.append(trace.run_id)

        tau, k, is_finite = compute_conformal_threshold(max_scores, self.alpha)

        return CalibratedThresholdRecord(
            alpha=self.alpha,
            sample_count=len(max_scores),
            k_order_statistic=k,
            threshold=tau,
            is_finite=is_finite,
            score_definition=score_name,
            calibration_run_ids=run_ids,
        )
