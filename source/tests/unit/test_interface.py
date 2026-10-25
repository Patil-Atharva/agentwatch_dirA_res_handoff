"""Unit tests for model and pre-execution interfaces."""

import pytest
from pydantic import ValidationError

from agentwatch_a.models.interface import BaseMonitorScorer, PreExecutionInput


def test_valid_pre_execution_input():
    event = PreExecutionInput(
        goal="Check my calendar for tomorrow.",
        step_index=0,
        prior_actions=[],
        prior_observations=[],
        proposed_tool="search_calendar",
        proposed_args={"date": "2026-10-24"},
    )
    assert event.proposed_tool == "search_calendar"
    assert event.step_index == 0


def test_pre_execution_input_forbids_post_execution_leakage():
    # Attempting to inject future observations or labels into PreExecutionInput must fail validation
    with pytest.raises(ValidationError):
        PreExecutionInput(
            goal="Goal",
            step_index=1,
            proposed_tool="tool",
            observation_after_execution="leaked_future_result",  # type: ignore
        )


def test_base_monitor_scorer_cannot_be_instantiated_directly():
    with pytest.raises(TypeError):
        BaseMonitorScorer()  # type: ignore