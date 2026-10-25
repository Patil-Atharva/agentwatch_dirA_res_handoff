"""Tool-transition Markov bigram baseline (B1).

Adheres to Section 8.1 and Section 8.4 of AGENTWATCH_DIRECTION_A_SPEC.md.
A fast, zero-parameter, deterministic anomaly detector based on tool transition statistics.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from typing import TYPE_CHECKING

from agentwatch_a.models.interface import BaseMonitorScorer, PreExecutionInput

if TYPE_CHECKING:
    from agentwatch_a.schemas import TrajectoryTrace

START_TOKEN = "<START>"


class ToolTransitionBaseline(BaseMonitorScorer):
    """Baseline B1: Scores tool calls by empirical transition rarity on benign traces."""

    def __init__(self, smoothing_alpha: float = 1.0):
        self.smoothing_alpha = smoothing_alpha
        self.transition_counts: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
        self.context_totals: dict[str, float] = defaultdict(float)
        self.known_tools: set[str] = set()
        self.is_fitted: bool = False

    def fit(self, benign_traces: Sequence[TrajectoryTrace]) -> ToolTransitionBaseline:
        """Fit transition probability distribution from benign training trajectories."""
        self.transition_counts.clear()
        self.context_totals.clear()
        self.known_tools.clear()

        for trace in benign_traces:
            if trace.trajectory_label != "BENIGN":
                continue

            prev_tool = START_TOKEN
            for step in trace.steps:
                curr_tool = step.proposed_action.tool
                self.known_tools.add(curr_tool)
                self.transition_counts[prev_tool][curr_tool] += 1.0
                self.context_totals[prev_tool] += 1.0
                prev_tool = curr_tool

        self.is_fitted = True
        return self

    def get_transition_probability(self, prev_tool: str, curr_tool: str) -> float:
        """Compute smoothed transition probability P(curr_tool | prev_tool)."""
        vocab_size = max(len(self.known_tools), 1)
        count = self.transition_counts[prev_tool][curr_tool]
        total = self.context_totals[prev_tool]
        return (count + self.smoothing_alpha) / (total + self.smoothing_alpha * vocab_size)

    def score_pre_execution(self, event_input: PreExecutionInput) -> float:
        """Assign anomaly score in [0.0, 1.0] to proposed tool call.

        Higher score indicates an unexpected or unseen tool transition.
        """
        if not self.is_fitted:
            return 0.5

        prev_tool = START_TOKEN
        if event_input.prior_actions:
            prev_tool = event_input.prior_actions[-1].get("tool", START_TOKEN)

        curr_tool = event_input.proposed_tool

        # 1. Unknown proposed tool is maximally anomalous
        if curr_tool not in self.known_tools:
            return 1.0

        # 2. Unknown previous tool context is highly anomalous
        if prev_tool != START_TOKEN and prev_tool not in self.known_tools:
            return 0.9

        prob = self.get_transition_probability(prev_tool, curr_tool)

        # Compute max possible probability from this context
        possible_tools = self.known_tools | {curr_tool}
        max_prob = max(self.get_transition_probability(prev_tool, t) for t in possible_tools)

        if max_prob <= 0.0:
            return 1.0

        relative_rarity = 1.0 - (prob / max_prob)
        return float(min(max(relative_rarity, 0.0), 1.0))

    def reset(self) -> None:
        """Reset sequential state (stateless model)."""
