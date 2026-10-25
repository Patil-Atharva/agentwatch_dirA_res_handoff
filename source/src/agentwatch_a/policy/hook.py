"""Pre-execution monitor hook for live benchmark integration.

Adheres strictly to Section 6.1 and Section 10.5 of AGENTWATCH_DIRECTION_A_SPEC.md.
Connects any BaseMonitorScorer and DecisionPolicy into the causal pre-execution
interception loop, measuring operational blocking and inference latency.
"""

from __future__ import annotations

import time

from pydantic import BaseModel, ConfigDict, Field

from agentwatch_a.models.interface import BaseMonitorScorer, PreExecutionInput
from agentwatch_a.policy.decision import DecisionPolicy, MonitorDecision


class PreExecutionHookTelemetry(BaseModel):
    """Telemetry report for in-loop pre-execution monitoring."""
    model_config = ConfigDict(extra="forbid")

    total_intercepted_calls: int = Field(default=0)
    allowed_calls: int = Field(default=0)
    blocked_calls: int = Field(default=0)
    held_calls: int = Field(default=0)
    flagged_calls: int = Field(default=0)
    mean_latency_ms: float = Field(default=0.0)
    max_latency_ms: float = Field(default=0.0)
    min_latency_ms: float = Field(default=0.0)


class PreExecutionMonitorHook:
    """Callable hook passed to PreExecutionInterceptor.on_pre_execution."""

    def __init__(
        self,
        scorer: BaseMonitorScorer,
        policy: DecisionPolicy,
        record_latencies: bool = True,
    ):
        self.scorer = scorer
        self.policy = policy
        self.record_latencies = record_latencies
        self.decisions: list[MonitorDecision] = []
        self.latencies_ms: list[float] = []

    def reset(self) -> None:
        """Reset internal state between runs."""
        self.scorer.reset()
        self.decisions.clear()
        self.latencies_ms.clear()

    def __call__(self, event_input: PreExecutionInput) -> bool:
        """Evaluate proposed action at pre-execution gate and decide allow/block."""
        t0 = time.perf_counter()
        risk_score = self.scorer.score_pre_execution(event_input)
        t1 = time.perf_counter()

        if self.record_latencies:
            self.latencies_ms.append((t1 - t0) * 1000.0)

        decision = self.policy.evaluate(event_input.step_index, risk_score)
        self.decisions.append(decision)

        # In active intervention mode: BLOCK or HOLD prevents tool dispatch
        return decision.action not in ("BLOCK", "HOLD")

    def get_telemetry(self) -> PreExecutionHookTelemetry:
        """Compile operational metrics and latency profile."""
        total = len(self.decisions)
        allowed = sum(1 for d in self.decisions if d.action == "ALLOW")
        blocked = sum(1 for d in self.decisions if d.action == "BLOCK")
        held = sum(1 for d in self.decisions if d.action == "HOLD")
        flagged = sum(1 for d in self.decisions if d.action == "FLAG")

        if self.latencies_ms:
            mean_lat = float(sum(self.latencies_ms) / len(self.latencies_ms))
            max_lat = float(max(self.latencies_ms))
            min_lat = float(min(self.latencies_ms))
        else:
            mean_lat = max_lat = min_lat = 0.0

        return PreExecutionHookTelemetry(
            total_intercepted_calls=total,
            allowed_calls=allowed,
            blocked_calls=blocked,
            held_calls=held,
            flagged_calls=flagged,
            mean_latency_ms=mean_lat,
            max_latency_ms=max_lat,
            min_latency_ms=min_lat,
        )
