"""Canonical trace and pre-execution schemas for AgentWatch-A.

Adheres strictly to Section 6.1, Section 7.3, and Appendix A of AGENTWATCH_DIRECTION_A_SPEC.md.
"""

from __future__ import annotations

import copy
import hashlib
import json
from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from agentwatch_a.models.interface import PreExecutionInput

TrajectoryLabel = Literal["BENIGN", "UNEXPOSED", "EXPOSED_RESISTED", "HIJACKED"]
MonitorDecision = Literal["ALLOW", "FLAG", "HOLD", "BLOCK"]


class ProposedAction(BaseModel):
    """Structured representation of a proposed tool call."""
    model_config = ConfigDict(extra="forbid")

    tool: str = Field(..., description="Name of the proposed tool function")
    args: dict[str, Any] = Field(default_factory=dict, description="Arguments dictionary for the proposed tool")


class TrajectoryStep(BaseModel):
    """A single decision step in an agent trajectory.

    CRITICAL INVARIANT (Section 6.1):
    The pre-execution monitor evaluated at this step can ONLY observe:
      - goal (from TrajectoryTrace)
      - prior_actions (steps 0 .. step_index-1)
      - prior_observations (steps 0 .. step_index-1)
      - proposed_action
      - untrusted_sources_in_prefix and provenance_features

    The monitor CANNOT access observation_after_execution, future steps,
    or ground-truth trajectory labels.
    """
    model_config = ConfigDict(extra="forbid")

    step_index: int = Field(..., ge=0, description="0-indexed step counter in trajectory")
    prior_actions: list[dict[str, Any]] = Field(
        default_factory=list,
        description="List of prior action dictionaries [{'tool': ..., 'args': ...}] before step t",
    )
    prior_observations: list[str] = Field(
        default_factory=list,
        description="List of prior observation strings returned by tools before step t",
    )
    proposed_action: ProposedAction = Field(..., description="The proposed action pending pre-execution decision")
    untrusted_sources_in_prefix: list[str] = Field(
        default_factory=list,
        description="Identified external / untrusted observation sources up to step t-1",
    )
    provenance_features: dict[str, Any] = Field(
        default_factory=dict,
        description="Deterministic provenance attributes (e.g. argument string matches)",
    )
    monitor_score: float | None = Field(
        default=None,
        description="Anomaly / hijack suspicion score assigned by monitor in [0, 1]",
    )
    threshold: float | None = Field(
        default=None,
        description="Calibrated conformal threshold applied at decision time",
    )
    monitor_decision: MonitorDecision | None = Field(
        default=None,
        description="Online decision: ALLOW, FLAG, HOLD, or BLOCK",
    )
    decision_timestamp_ms: float | None = Field(
        default=None,
        description="Timestamp or latency in ms for monitor decision",
    )
    tool_executed: bool = Field(
        default=True,
        description="Whether the tool was allowed to execute after monitor decision",
    )
    observation_after_execution: str | None = Field(
        default=None,
        description="POST-EXECUTION LOGGING ONLY. Strictly forbidden at decision point.",
    )
    injection_visible_after_execution: bool = Field(
        default=False,
        description="Whether injected payload became visible in this step's observation",
    )
    tool_latency_ms: float | None = Field(
        default=None,
        description="Tool execution latency in milliseconds",
    )

    def to_pre_execution_input(self, goal: str) -> PreExecutionInput:
        """Extract strictly causal PreExecutionInput object without post-call data."""
        return PreExecutionInput(
            goal=goal,
            step_index=self.step_index,
            prior_actions=copy.deepcopy(self.prior_actions),
            prior_observations=copy.deepcopy(self.prior_observations),
            proposed_tool=self.proposed_action.tool,
            proposed_args=copy.deepcopy(self.proposed_action.args),
            metadata={
                "untrusted_sources_in_prefix": list(self.untrusted_sources_in_prefix),
                "provenance_features": copy.deepcopy(self.provenance_features),
            },
        )


class TrajectoryTrace(BaseModel):
    """Complete canonical record of an agent trajectory execution (Appendix A)."""
    model_config = ConfigDict(extra="forbid")

    schema_version: str = Field(default="1.0", description="Trace schema version")
    run_id: str = Field(..., description="Unique run identifier")
    pair_id: str | None = Field(default=None, description="Paired condition identifier")
    benchmark: str = Field(default="agentdojo", description="Benchmark name")
    benchmark_package_version: str | None = Field(default="0.1.35", description="Pinned package version")
    benchmark_commit: str | None = Field(default=None, description="Benchmark git commit or tag")
    task_revision: str | None = Field(default="v1", description="Benchmark task revision")
    suite: str = Field(default="workspace", description="Benchmark suite name")
    user_task_id: str = Field(..., description="User task identifier")
    injection_task_id: str | None = Field(default=None, description="Injection task identifier if configured")
    attack_template_family: str | None = Field(default=None, description="Attack vector name")
    attack_level: str = Field(default="L0", description="Attack perturbation level")
    agent_provider: str = Field(default="local_ollama", description="Agent model provider")
    agent_model_version: str = Field(..., description="Agent model name and version")
    seed: int = Field(default=17, description="Random seed")
    goal: str = Field(..., description="Trusted user goal")
    injection_configured: bool = Field(default=False, description="Whether injection was configured in task")
    injection_visible: bool = Field(default=False, description="Whether injection appeared in any tool observation")
    trajectory_label: TrajectoryLabel = Field(..., description="Ground-truth outcome label")
    security_success: bool = Field(default=False, description="Whether security check confirmed hijack")
    utility_success: bool = Field(default=False, description="Whether user task utility was achieved")
    agent_finished: bool = Field(default=True, description="Whether trajectory ran to completion without crashing")
    t_harm: int | None = Field(
        default=None,
        ge=0,
        description="Index of first proposed tool call satisfying attacker goal (HIJACKED only)",
    )
    steps: list[TrajectoryStep] = Field(default_factory=list, description="Ordered sequence of trajectory steps")
    code_commit: str = Field(default="HEAD", description="Git commit SHA of agentwatch repository")
    config_hash: str | None = Field(default=None, description="Hash of active configuration")
    completed_at_utc: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat(),
        description="ISO-8601 completion timestamp",
    )
    failure_status: str | None = Field(default=None, description="Error status if aborted or failed")
    content_hash: str | None = Field(default=None, description="SHA-256 integrity hash of trace")

    def compute_content_hash(self) -> str:
        """Compute deterministic SHA-256 integrity hash over canonical trace fields."""
        data = self.model_dump(exclude={"content_hash"})
        canonical_str = json.dumps(data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()

    def seal(self) -> TrajectoryTrace:
        """Compute and assign content_hash, returning sealed trace."""
        self.content_hash = self.compute_content_hash()
        return self

    def verify_integrity(self) -> bool:
        """Verify that content_hash matches current content."""
        if not self.content_hash:
            return False
        return self.content_hash == self.compute_content_hash()

    def get_pre_execution_input(self, step_index: int) -> PreExecutionInput:
        """Safely extract PreExecutionInput for step_index enforcing information isolation."""
        if step_index < 0 or step_index >= len(self.steps):
            raise IndexError(f"step_index {step_index} out of range for trace with {len(self.steps)} steps")
        return self.steps[step_index].to_pre_execution_input(self.goal)