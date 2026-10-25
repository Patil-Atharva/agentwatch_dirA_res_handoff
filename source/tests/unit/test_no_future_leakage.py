"""Unit tests verifying strict absence of temporal leakage and valid causal prefixing.

Adheres strictly to Section 6.1 and Section 7.3 of AGENTWATCH_DIRECTION_A_SPEC.md.
"""

from __future__ import annotations

import pytest

from agentwatch_a.schemas import ProposedAction, TrajectoryStep, TrajectoryTrace
from agentwatch_a.trace_store import validate_trajectory


def create_valid_two_step_benign_trace() -> TrajectoryTrace:
    return TrajectoryTrace(
        run_id="valid-run-001",
        user_task_id="user_task_0",
        agent_model_version="local_test",
        goal="Search messages and print count.",
        trajectory_label="BENIGN",
        steps=[
            TrajectoryStep(
                step_index=0,
                prior_actions=[],
                prior_observations=[],
                proposed_action=ProposedAction(tool="search_emails", args={"query": "hello"}),
                observation_after_execution="Found 2 emails",
            ),
            TrajectoryStep(
                step_index=1,
                prior_actions=[{"tool": "search_emails", "args": {"query": "hello"}}],
                prior_observations=["Found 2 emails"],
                proposed_action=ProposedAction(tool="get_current_day", args={}),
                observation_after_execution="2024-05-15",
            ),
        ],
    )


def test_valid_trace_passes_validation() -> None:
    trace = create_valid_two_step_benign_trace()
    errors = validate_trajectory(trace)
    assert errors == []


def test_future_observation_leakage_detected() -> None:
    trace = create_valid_two_step_benign_trace()
    # Violate causality: step 0 attempts to sneak in observation 0 in its prior_observations
    trace.steps[0].prior_observations = ["Found 2 emails"]
    errors = validate_trajectory(trace)
    assert any("prior_observations, expected 0" in err for err in errors)


def test_mismatched_prior_actions_detected() -> None:
    trace = create_valid_two_step_benign_trace()
    # Step 1 claims step 0 was a delete action instead of search_emails
    trace.steps[1].prior_actions = [{"tool": "delete_all", "args": {}}]
    errors = validate_trajectory(trace)
    assert any("does not match proposed action of step 0" in err for err in errors)


def test_non_sequential_step_index_detected() -> None:
    trace = create_valid_two_step_benign_trace()
    trace.steps[1].step_index = 5
    errors = validate_trajectory(trace)
    assert any("mismatched step_index=5" in err for err in errors)


def test_label_consistency_benign_with_injection() -> None:
    trace = create_valid_two_step_benign_trace()
    trace.injection_configured = True
    errors = validate_trajectory(trace)
    assert any("BENIGN trace cannot have injection_configured=True" in err for err in errors)


def test_label_consistency_hijacked_missing_t_harm() -> None:
    trace = create_valid_two_step_benign_trace()
    trace.trajectory_label = "HIJACKED"
    trace.injection_configured = True
    trace.injection_visible = True
    trace.steps[0].injection_visible_after_execution = True
    trace.security_success = True
    trace.t_harm = None  # Missing t_harm
    errors = validate_trajectory(trace)
    assert any("HIJACKED trace must specify t_harm" in err for err in errors)


def test_label_consistency_hijacked_out_of_bounds_t_harm() -> None:
    trace = create_valid_two_step_benign_trace()
    trace.trajectory_label = "HIJACKED"
    trace.injection_configured = True
    trace.injection_visible = True
    trace.steps[0].injection_visible_after_execution = True
    trace.security_success = True
    trace.t_harm = 10  # Trace has only 2 steps
    errors = validate_trajectory(trace)
    assert any("out of range" in err for err in errors)


def test_get_pre_execution_input_boundary() -> None:
    trace = create_valid_two_step_benign_trace()
    inp0 = trace.get_pre_execution_input(0)
    assert inp0.step_index == 0
    assert inp0.prior_actions == []
    assert inp0.prior_observations == []
    assert inp0.proposed_tool == "search_emails"

    inp1 = trace.get_pre_execution_input(1)
    assert inp1.step_index == 1
    assert len(inp1.prior_actions) == 1
    assert len(inp1.prior_observations) == 1
    assert inp1.proposed_tool == "get_current_day"

    with pytest.raises(IndexError):
        trace.get_pre_execution_input(2)
