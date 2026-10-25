"""Unconditioned causal sequence model baseline (B4).

Adheres strictly to Section 11.1 of AGENTWATCH_DIRECTION_A_SPEC.md.
Models sequential action dynamics across the entire trajectory prefix
WITHOUT goal conditioning (isolating hypothesis H2 / RQ-A4).
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from typing import TYPE_CHECKING

from agentwatch_a.models.interface import BaseMonitorScorer, PreExecutionInput

if TYPE_CHECKING:
    from agentwatch_a.schemas import TrajectoryTrace

START_TOKEN = "<START>"


class UnconditionedSequenceBaseline(BaseMonitorScorer):
    """Baseline B4: Models sequential tool calling patterns WITHOUT goal conditioning.

    Tests Hypothesis H2:
    Demonstrates whether a sequence-aware model without goal alignment
    can detect attacks or whether goal conditioning is strictly necessary.
    """

    def __init__(self, smoothing_alpha: float = 1.0, max_order: int = 3):
        self.smoothing_alpha = smoothing_alpha
        self.max_order = max_order
        self.ngram_counts: dict[tuple[str, ...], dict[str, float]] = defaultdict(lambda: defaultdict(float))
        self.context_totals: dict[tuple[str, ...], float] = defaultdict(float)
        self.vocab: set[str] = set()
        self.is_fitted: bool = False

    def fit(self, benign_traces: Sequence[TrajectoryTrace]) -> UnconditionedSequenceBaseline:
        """Fit sequential n-gram transitions on benign trajectories."""
        self.ngram_counts.clear()
        self.context_totals.clear()
        self.vocab.clear()

        for trace in benign_traces:
            if trace.trajectory_label != "BENIGN":
                continue

            tool_seq: list[str] = [step.proposed_action.tool for step in trace.steps]
            for tool in tool_seq:
                self.vocab.add(tool)

            padded_seq = [START_TOKEN] * (self.max_order - 1) + tool_seq

            for i in range(len(tool_seq)):
                target_idx = i + (self.max_order - 1)
                target_tool = padded_seq[target_idx]

                for order in range(1, self.max_order + 1):
                    start_idx = target_idx - (order - 1)
                    context = tuple(padded_seq[start_idx:target_idx])
                    self.ngram_counts[context][target_tool] += 1.0
                    self.context_totals[context] += 1.0

        self.is_fitted = True
        return self

    def _score_transition(self, context: tuple[str, ...], target_tool: str) -> float:
        """Compute smoothed probability of target_tool given context."""
        vocab_size = max(len(self.vocab), 1)
        count = self.ngram_counts[context][target_tool]
        total = self.context_totals[context]
        return (count + self.smoothing_alpha) / (total + self.smoothing_alpha * vocab_size)

    def score_pre_execution(self, event_input: PreExecutionInput) -> float:
        """Score sequential surprise of proposed tool given prior action sequence.

        CRITICAL REQUIREMENT:
        Does NOT inspect event_input.goal.
        """
        if not self.is_fitted:
            return 0.5

        prior_tools = [act.get("tool", "") for act in event_input.prior_actions if act.get("tool")]
        curr_tool = event_input.proposed_tool

        padded = [START_TOKEN] * (self.max_order - 1) + prior_tools
        target_idx = len(padded)

        weights = [0.2, 0.3, 0.5] if self.max_order == 3 else [1.0 / self.max_order] * self.max_order
        interpolated_prob = 0.0

        for order_idx, order in enumerate(range(1, self.max_order + 1)):
            start_idx = target_idx - (order - 1)
            ctx = tuple(padded[start_idx:target_idx])
            p_order = self._score_transition(ctx, curr_tool)
            interpolated_prob += weights[order_idx] * p_order

        best_ctx = tuple(padded[target_idx - (self.max_order - 1):target_idx])
        all_candidates = self.vocab | {curr_tool}
        max_p = max(self._score_transition(best_ctx, t) for t in all_candidates)

        if max_p <= 0.0:
            return 1.0

        rarity = 1.0 - (interpolated_prob / max_p)
        return float(min(max(rarity, 0.0), 1.0))

    def reset(self) -> None:
        """Reset internal sequential state (stateless across trajectories)."""
