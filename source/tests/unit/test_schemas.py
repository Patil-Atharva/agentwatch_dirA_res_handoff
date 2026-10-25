"""Unit tests for canonical trace schemas and cryptographic integrity.

Adheres to Section 6.1, Section 7.6, and Appendix A of AGENTWATCH_DIRECTION_A_SPEC.md.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from agentwatch_a.schemas import ProposedAction, TrajectoryStep, TrajectoryTrace


def test_proposed_action_schema() -> None:
    action = ProposedAction(tool="search_emails", args={"query": "test"})
    assert action.tool == "search_emails"
    assert action.args == {"query": "test"}

    # Extra fields are strictly forbidden
    with pytest.raises(ValidationError):
        ProposedAction.model_validate({"tool": "search_emails", "args": {}, "extra_field": 123})


def test_trajectory_step_to_pre_execution_input_isolation() -> None:
    step = TrajectoryStep(
        step_index=1,
        prior_actions=[{"tool": "get_unread_emails", "args": {}}],
        prior_observations=["Observation 0"],
        proposed_action=ProposedAction(tool="send_email", args={"recipient": "test@example.com"}),
        observation_after_execution="Email sent successfully",
        injection_visible_after_execution=False,
    )

    inp = step.to_pre_execution_input(goal="Send a status update email.")
    assert inp.goal == "Send a status update email."
    assert inp.step_index == 1
    assert len(inp.prior_actions) == 1
    assert len(inp.prior_observations) == 1
    assert inp.proposed_tool == "send_email"
    assert inp.proposed_args == {"recipient": "test@example.com"}

    # PreExecutionInput must NOT contain post-execution fields
    assert not hasattr(inp, "observation_after_execution")
    assert not hasattr(inp, "injection_visible_after_execution")
    assert not hasattr(inp, "trajectory_label")
    assert not hasattr(inp, "security_success")


def test_trace_content_hash_and_tamper_detection() -> None:
    trace = TrajectoryTrace(
        run_id="test-run-123",
        user_task_id="user_task_0",
        agent_model_version="local_qwen",
        goal="Test user goal",
        trajectory_label="BENIGN",
        steps=[],
    )

    assert trace.content_hash is None
    assert not trace.verify_integrity()

    # Seal trace
    trace.seal()
    assert trace.content_hash is not None
    assert trace.verify_integrity()

    # Tamper with a field
    trace.goal = "TAMPERED user goal"
    assert not trace.verify_integrity()


def test_extra_fields_forbidden_in_trace() -> None:
    data = {
        "run_id": "test-run-1",
        "user_task_id": "task_0",
        "agent_model_version": "qwen2.5:3b",
        "goal": "Goal",
        "trajectory_label": "BENIGN",
        "unauthorized_field": "leakage",
    }
    with pytest.raises(ValidationError):
        TrajectoryTrace.model_validate(data)
