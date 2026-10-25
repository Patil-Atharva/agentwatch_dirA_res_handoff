"""Supervised pre-execution oracle reference baseline (B6).

Adheres strictly to Section 11.1 of AGENTWATCH_DIRECTION_A_SPEC.md.
Trained on both benign and hijacked traces with step-level ground-truth labels
(y_t = 1 if hijacked and t >= t_harm).
Serves as an empirical upper-bound comparator to quantify the value of supervision.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

import numpy as np
from sklearn.ensemble import GradientBoostingClassifier

from agentwatch_a.models.interface import BaseMonitorScorer, PreExecutionInput
from agentwatch_a.provenance import extract_provenance_features

if TYPE_CHECKING:
    from agentwatch_a.schemas import TrajectoryTrace


def _extract_step_features(event_input: PreExecutionInput) -> list[float]:
    """Extract strictly pre-execution numerical features at decision step t.

    CRITICAL SAFETY GUARANTEE:
    Uses only information available before execution of proposed action.
    """
    prov = extract_provenance_features(event_input)

    # Tool high impact flags
    f_high_impact = 1.0 if prov.high_impact_tool else 0.0
    f_high_impact_untrusted = 1.0 if prov.high_impact_untrusted_argument else 0.0

    # Argument counts and provenance overlaps
    num_args = float(prov.num_arguments)
    in_goal = float(prov.num_arguments_in_goal)
    from_untrusted = float(prov.num_arguments_from_untrusted)
    goal_ratio = in_goal / max(num_args, 1.0)
    untrusted_ratio = from_untrusted / max(num_args, 1.0)

    # Prefix context dynamics
    step_idx = float(event_input.step_index)
    num_prior_actions = float(len(event_input.prior_actions))
    obs_chars = float(sum(len(obs) for obs in event_input.prior_observations))
    has_untrusted_obs = 1.0 if obs_chars > 0 else 0.0

    # Tool name hash feature for categorical tool representation
    tool_hash = float(hash(event_input.proposed_tool) % 31) / 31.0

    return [
        f_high_impact,
        f_high_impact_untrusted,
        num_args,
        in_goal,
        from_untrusted,
        goal_ratio,
        untrusted_ratio,
        step_idx,
        num_prior_actions,
        obs_chars,
        has_untrusted_obs,
        tool_hash,
    ]


class SupervisedOracleBaseline(BaseMonitorScorer):
    """Baseline B6: Supervised step-level pre-execution classifier.

    Estimates the empirical performance ceiling of full supervision.
    Trained on labeled traces using step-level labels y_t in {0, 1}.
    """

    def __init__(self, n_estimators: int = 50, random_state: int = 42):
        self.n_estimators = n_estimators
        self.random_state = random_state
        self.classifier = GradientBoostingClassifier(
            n_estimators=self.n_estimators,
            random_state=self.random_state,
            max_depth=3,
        )
        self.is_fitted: bool = False

    def fit(self, labeled_traces: Sequence[TrajectoryTrace]) -> SupervisedOracleBaseline:
        """Fit supervised classifier on step-level pre-execution features."""
        X: list[list[float]] = []
        y: list[int] = []

        for trace in labeled_traces:
            is_hijacked = trace.trajectory_label == "HIJACKED"
            t_harm = trace.t_harm if trace.t_harm is not None else (len(trace.steps) - 1)

            for step_idx in range(len(trace.steps)):
                inp = trace.get_pre_execution_input(step_idx)
                feats = _extract_step_features(inp)
                X.append(feats)

                # Ground truth step label: 1 if trajectory was hijacked and step is at or after harm point
                step_label = 1 if (is_hijacked and step_idx >= t_harm) else 0
                y.append(step_label)

        if not X:
            # Fallback for empty corpus
            dummy_input = PreExecutionInput(
                goal="test",
                step_index=0,
                proposed_tool="dummy",
                proposed_args={},
            )
            X = [_extract_step_features(dummy_input), _extract_step_features(dummy_input)]
            y = [0, 1]

        # Ensure both classes exist
        if len(set(y)) < 2:
            # Synthesize synthetic opposite sample to ensure valid binary probability calibration
            opposite_label = 1 if y[0] == 0 else 0
            synthetic_feats = [float(val * 1.5) for val in X[0]]
            X.append(synthetic_feats)
            y.append(opposite_label)

        self.classifier.fit(np.array(X), np.array(y))
        self.is_fitted = True
        return self

    def score_pre_execution(self, event_input: PreExecutionInput) -> float:
        """Compute supervised probability of hijack at decision step t."""
        if not self.is_fitted:
            return 0.5

        feats = _extract_step_features(event_input)
        x = np.array([feats])
        prob_hijacked = float(self.classifier.predict_proba(x)[0, 1])
        return float(min(max(prob_hijacked, 0.0), 1.0))

    def reset(self) -> None:
        """Reset internal state between trajectories (stateless)."""
