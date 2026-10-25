"""Integration tests for canonical trace serialization, deserialization, and roundtrip.

Adheres strictly to Section 6.1 and Appendix A of AGENTWATCH_DIRECTION_A_SPEC.md.
"""

from __future__ import annotations

from pathlib import Path

from agentwatch_a.benchmark.agentdojo_adapter import AgentDojoAdapter
from agentwatch_a.schemas import TrajectoryTrace
from agentwatch_a.trace_store import (
    append_trace_to_jsonl,
    load_traces_from_jsonl,
    save_traces_to_jsonl,
    validate_trace_file,
)


def test_fixture_traces_load_and_validate() -> None:
    fixture_path = Path("tests/fixtures/tiny_synthetic_traces.jsonl")
    assert fixture_path.exists()

    traces = load_traces_from_jsonl(fixture_path, validate=True)
    assert len(traces) == 4

    labels = [t.trajectory_label for t in traces]
    assert labels == ["BENIGN", "UNEXPOSED", "EXPOSED_RESISTED", "HIJACKED"]

    # All fixture traces must verify their cryptographic content hashes
    for t in traces:
        assert t.verify_integrity()


def test_roundtrip_save_and_load(tmp_path: Path) -> None:
    trace_file = tmp_path / "test_traces.jsonl"
    fixture_path = Path("tests/fixtures/tiny_synthetic_traces.jsonl")
    original_traces = load_traces_from_jsonl(fixture_path, validate=True)

    # Save to new destination
    saved_count = save_traces_to_jsonl(original_traces, trace_file, overwrite=True, seal=True)
    assert saved_count == 4

    # Load back and verify equality
    reloaded_traces = load_traces_from_jsonl(trace_file, validate=True)
    assert len(reloaded_traces) == 4
    for orig, reloaded in zip(original_traces, reloaded_traces):
        assert orig.run_id == reloaded.run_id
        assert orig.trajectory_label == reloaded.trajectory_label
        assert orig.content_hash == reloaded.content_hash
        assert reloaded.verify_integrity()


def test_append_trace(tmp_path: Path) -> None:
    trace_file = tmp_path / "append_test.jsonl"
    trace1 = TrajectoryTrace(
        run_id="run-1",
        user_task_id="task_0",
        agent_model_version="mock",
        goal="Task 1",
        trajectory_label="BENIGN",
        steps=[],
    )
    trace2 = TrajectoryTrace(
        run_id="run-2",
        user_task_id="task_1",
        agent_model_version="mock",
        goal="Task 2",
        trajectory_label="BENIGN",
        steps=[],
    )

    append_trace_to_jsonl(trace1, trace_file)
    append_trace_to_jsonl(trace2, trace_file)

    loaded = load_traces_from_jsonl(trace_file)
    assert len(loaded) == 2
    assert [t.run_id for t in loaded] == ["run-1", "run-2"]


def test_live_benchmark_run_to_canonical_trace(tmp_path: Path) -> None:
    """Verify live execution result converts to sealed canonical trace passing full validation."""
    adapter = AgentDojoAdapter(benchmark_version="v1", suite_name="workspace")
    run_result = adapter.run_case(
        user_task_id="user_task_0",
        mock_tool_sequence=[("search_emails", {"query": "test"})],
    )

    canonical_trace = run_result.to_canonical_trace()
    assert canonical_trace.run_id == run_result.run_id
    assert canonical_trace.trajectory_label == "BENIGN"
    assert canonical_trace.verify_integrity()

    # Save and reload
    trace_file = tmp_path / "benchmark_trace.jsonl"
    save_traces_to_jsonl([canonical_trace], trace_file, overwrite=True)

    loaded = load_traces_from_jsonl(trace_file, validate=True)
    assert len(loaded) == 1
    assert loaded[0].run_id == canonical_trace.run_id
    assert loaded[0].verify_integrity()


def test_validate_corrupted_trace_file(tmp_path: Path) -> None:
    corrupted_file = tmp_path / "corrupted.jsonl"
    with open(corrupted_file, "w", encoding="utf-8") as f:
        f.write('{"schema_version": "1.0", "run_id": "r1", "invalid_json": \n')

    total, valid, errors = validate_trace_file(corrupted_file)
    assert total == 1
    assert valid == 0
    assert len(errors) == 1
    assert "Malformed" in errors[0]
