"""Runtime decision policy and threshold enforcement for AgentWatch-A.

Adheres strictly to Section 9.5 of AGENTWATCH_DIRECTION_A_SPEC.md.
Evaluates pre-execution risk scores against frozen calibrated thresholds,
issuing ALLOW, FLAG, HOLD, or BLOCK operational actions.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

DecisionAction = Literal["ALLOW", "FLAG", "HOLD", "BLOCK"]
PolicyMode = Literal["detect_only", "active_intervention"]


class MonitorDecision(BaseModel):
    """Structured decision issued at the pre-execution boundary."""
    model_config = ConfigDict(extra="forbid")

    step_index: int = Field(ge=0, description="Step index where decision was made.")
    risk_score: float = Field(ge=0.0, le=1.0, description="Monitor pre-execution risk score.")
    threshold: float = Field(description="Frozen calibrated decision threshold.")
    action: DecisionAction = Field(description="Operational decision (ALLOW, FLAG, HOLD, BLOCK).")
    mode: PolicyMode = Field(description="Enforcement mode (detect_only or active_intervention).")
    is_alert: bool = Field(description="True if risk_score strictly exceeds threshold.")
    reason: str = Field(description="Human-readable decision explanation.")


class DecisionPolicy:
    """Applies calibrated thresholds to pre-execution risk scores."""

    def __init__(
        self,
        threshold: float,
        mode: PolicyMode = "detect_only",
        active_action: Literal["HOLD", "BLOCK"] = "BLOCK",
    ):
        self.threshold = threshold
        self.mode = mode
        self.active_action = active_action

    def evaluate(self, step_index: int, risk_score: float) -> MonitorDecision:
        """Evaluate risk score against frozen threshold."""
        is_alert = risk_score > self.threshold

        if not is_alert:
            action: DecisionAction = "ALLOW"
            reason = f"Risk score ({risk_score:.4f}) is at or below threshold ({self.threshold:.4f})."
        else:
            if self.mode == "detect_only":
                action = "FLAG"
                reason = f"ALERT: Risk score ({risk_score:.4f}) exceeds threshold ({self.threshold:.4f}) in detect-only mode."
            else:
                action = self.active_action
                reason = f"INTERVENTION: Risk score ({risk_score:.4f}) exceeds threshold ({self.threshold:.4f}) -> {self.active_action} proposed action."

        return MonitorDecision(
            step_index=step_index,
            risk_score=risk_score,
            threshold=self.threshold,
            action=action,
            mode=self.mode,
            is_alert=is_alert,
            reason=reason,
        )
