"""Abstract interfaces and base contracts for AgentWatch-A models and baselines.

Enforces Section 6.1 (pre-execution boundary) and Section 8 (model specification).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PreExecutionInput(BaseModel):
    """Encapsulates strictly pre-execution information available at decision step t.

    CRITICAL SAFETY INVARIANT (Section 6.1):
    Contains NO future steps, NO observation resulting from the current action,
    and NO ground-truth labels.
    """
    model_config = ConfigDict(extra="forbid")

    goal: str = Field(description="Trusted user goal.")
    step_index: int = Field(ge=0, description="Current step index (0-based or 1-based).")
    prior_actions: list[dict[str, Any]] = Field(
        default_factory=list,
        description="List of prior executed tool calls [(tool, args), ...]."
    )
    prior_observations: list[str] = Field(
        default_factory=list,
        description="List of prior tool output strings."
    )
    proposed_tool: str = Field(description="Proposed tool name about to be executed.")
    proposed_args: dict[str, Any] = Field(
        default_factory=dict,
        description="Proposed tool call arguments."
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Policy or trust metadata (e.g. untrusted sources in prefix)."
    )


class BaseMonitorScorer(ABC):
    """Abstract base class for all pre-execution monitors and baselines."""

    @abstractmethod
    def score_pre_execution(self, event_input: PreExecutionInput) -> float:
        """Compute an anomaly / risk score for the proposed tool call.

        Args:
            event_input: Strongly validated pre-execution input.

        Returns:
            A float risk score where higher indicates greater anomaly/risk.
        """

    @abstractmethod
    def reset(self) -> None:
        """Reset internal sequential state between trajectories."""
