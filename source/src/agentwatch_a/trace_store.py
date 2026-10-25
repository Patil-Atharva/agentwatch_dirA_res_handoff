"""Streaming JSONL trace storage and validation utilities for AgentWatch-A.

Adheres strictly to Section 6.1, Section 7.6, and Appendix A of AGENTWATCH_DIRECTION_A_SPEC.md.
"""

from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Iterator, Sequence
from pathlib import Path

import pydantic

from agentwatch_a.schemas import TrajectoryTrace


class TraceValidationError(Exception):
    """Raised when a trace fails schema or causality validation."""
    def __init__(self, message: str, errors: list[str]):
        super().__init__(f"{message}: {'; '.join(errors)}")
        self.errors = errors


def validate_trajectory(trace: TrajectoryTrace) -> list[str]:
    """Validate a TrajectoryTrace against temporal causality, information isolation, and label invariants.

    Returns a list of violation error strings (empty if trace is strictly valid).
    """
    errors: list[str] = []

    # 1. Schema version and base identity
    if trace.schema_version != "1.0":
        errors.append(f"Invalid schema_version '{trace.schema_version}', expected '1.0'")
    if not trace.run_id or not trace.run_id.strip():
        errors.append("run_id cannot be empty")
    if not trace.goal or not trace.goal.strip():
        errors.append("goal cannot be empty")
    if not trace.user_task_id or not trace.user_task_id.strip():
        errors.append("user_task_id cannot be empty")

    # 2. Label consistency (Section 7.3)
    if trace.trajectory_label == "BENIGN":
        if trace.injection_configured:
            errors.append("BENIGN trace cannot have injection_configured=True")
        if trace.injection_task_id is not None:
            errors.append(f"BENIGN trace cannot have injection_task_id='{trace.injection_task_id}'")
        if trace.injection_visible:
            errors.append("BENIGN trace cannot have injection_visible=True")
        if trace.t_harm is not None:
            errors.append("BENIGN trace cannot have t_harm set")

    elif trace.trajectory_label == "UNEXPOSED":
        if not trace.injection_configured:
            errors.append("UNEXPOSED trace must have injection_configured=True")
        if trace.injection_visible:
            errors.append("UNEXPOSED trace cannot have injection_visible=True")
        if trace.security_success:
            errors.append("UNEXPOSED trace cannot have security_success=True")
        if trace.t_harm is not None:
            errors.append("UNEXPOSED trace cannot have t_harm set")

    elif trace.trajectory_label == "EXPOSED_RESISTED":
        if not trace.injection_configured:
            errors.append("EXPOSED_RESISTED trace must have injection_configured=True")
        if not trace.injection_visible:
            errors.append("EXPOSED_RESISTED trace must have injection_visible=True")
        if trace.security_success:
            errors.append("EXPOSED_RESISTED trace cannot have security_success=True")
        if trace.t_harm is not None:
            errors.append("EXPOSED_RESISTED trace cannot have t_harm set")

    elif trace.trajectory_label == "HIJACKED":
        if not trace.injection_configured:
            errors.append("HIJACKED trace must have injection_configured=True")
        if not trace.injection_visible:
            errors.append("HIJACKED trace must have injection_visible=True")
        if not trace.security_success:
            errors.append("HIJACKED trace must have security_success=True")
        if trace.t_harm is None:
            errors.append("HIJACKED trace must specify t_harm")
        elif trace.t_harm < 0 or (trace.steps and trace.t_harm >= len(trace.steps)):
            errors.append(f"HIJACKED trace t_harm={trace.t_harm} out of range [0, {len(trace.steps)-1}]")

    # 3. Temporal causality & prefix integrity (Section 6.1)
    for idx, step in enumerate(trace.steps):
        if step.step_index != idx:
            errors.append(f"Step at index {idx} has mismatched step_index={step.step_index}")

        # Check prefix length
        if len(step.prior_actions) != idx:
            errors.append(
                f"Step {idx} has {len(step.prior_actions)} prior_actions, expected {idx}"
            )
        if len(step.prior_observations) != idx:
            errors.append(
                f"Step {idx} has {len(step.prior_observations)} prior_observations, expected {idx}"
            )

        # Check prefix consistency with preceding steps
        for p_idx in range(min(idx, len(step.prior_actions))):
            preceding_action = {
                "tool": trace.steps[p_idx].proposed_action.tool,
                "args": trace.steps[p_idx].proposed_action.args,
            }
            if step.prior_actions[p_idx] != preceding_action:
                errors.append(
                    f"Step {idx} prior_actions[{p_idx}] does not match proposed action of step {p_idx}"
                )

        for p_idx in range(min(idx, len(step.prior_observations))):
            expected_obs = trace.steps[p_idx].observation_after_execution or ""
            actual_obs = step.prior_observations[p_idx]
            if actual_obs != expected_obs:
                errors.append(
                    f"Step {idx} prior_observations[{p_idx}] does not match observation of step {p_idx}"
                )

        # Information isolation: ensure proposed tool has non-empty name
        if not step.proposed_action.tool or not step.proposed_action.tool.strip():
            errors.append(f"Step {idx} proposed_action has empty tool name")

    # 4. Exposure tracking consistency
    step_exposures = [s.injection_visible_after_execution for s in trace.steps]
    if trace.injection_visible and not any(step_exposures):
        errors.append("trace.injection_visible=True but no step recorded injection_visible_after_execution=True")
    if not trace.injection_visible and any(step_exposures):
        errors.append("trace.injection_visible=False but at least one step recorded injection_visible_after_execution=True")

    # 5. Content integrity verification
    if trace.content_hash is not None and not trace.verify_integrity():
        errors.append("Cryptographic content_hash mismatch: trace data has been altered after sealing")

    return errors


def save_traces_to_jsonl(
    traces: Sequence[TrajectoryTrace],
    path: Path | str,
    overwrite: bool = False,
    seal: bool = True,
    validate: bool = True,
) -> int:
    """Save a collection of traces to a JSONL file using atomic write."""
    target_path = Path(path).resolve()
    if target_path.exists() and not overwrite:
        raise FileExistsError(f"Target file already exists: {target_path}")

    target_path.parent.mkdir(parents=True, exist_ok=True)

    # Validate before writing
    if validate:
        for trace in traces:
            errs = validate_trajectory(trace)
            if errs:
                raise TraceValidationError(f"Cannot save invalid trace {trace.run_id}", errs)

    # Atomic write to temporary file
    temp_dir = target_path.parent
    fd, temp_file = tempfile.mkstemp(dir=temp_dir, prefix="traces_", suffix=".tmp")
    count = 0
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            for trace in traces:
                if seal:
                    trace.seal()
                line = trace.model_dump_json()
                f.write(line + "\n")
                count += 1
        # Atomic replace
        os.replace(temp_file, target_path)
    except Exception:
        if os.path.exists(temp_file):
            os.remove(temp_file)
        raise

    return count


def append_trace_to_jsonl(
    trace: TrajectoryTrace,
    path: Path | str,
    seal: bool = True,
    validate: bool = True,
) -> None:
    """Append a single trace to a JSONL file."""
    target_path = Path(path).resolve()
    target_path.parent.mkdir(parents=True, exist_ok=True)

    if validate:
        errs = validate_trajectory(trace)
        if errs:
            raise TraceValidationError(f"Cannot append invalid trace {trace.run_id}", errs)

    if seal:
        trace.seal()

    with open(target_path, "a", encoding="utf-8") as f:
        f.write(trace.model_dump_json() + "\n")


def stream_traces_from_jsonl(
    path: Path | str,
    validate: bool = True,
) -> Iterator[TrajectoryTrace]:
    """Stream TrajectoryTrace objects one by one from a JSONL file."""
    target_path = Path(path).resolve()
    if not target_path.exists():
        raise FileNotFoundError(f"Trace file not found: {target_path}")

    with open(target_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                raw_data = json.loads(stripped)
                trace = TrajectoryTrace.model_validate(raw_data)
            except Exception as e:
                raise ValueError(f"Failed parsing trace on line {line_num} of {target_path}: {e}") from e

            if validate:
                errs = validate_trajectory(trace)
                if errs:
                    raise TraceValidationError(f"Validation failed on line {line_num} ({trace.run_id})", errs)

            yield trace


def load_traces_from_jsonl(
    path: Path | str,
    validate: bool = True,
) -> list[TrajectoryTrace]:
    """Load and validate all traces from a JSONL file into memory."""
    return list(stream_traces_from_jsonl(path, validate=validate))


def validate_trace_file(path: Path | str) -> tuple[int, int, list[str]]:
    """Audit all traces in a JSONL file and return (total_count, valid_count, list_of_errors)."""
    target_path = Path(path).resolve()
    if not target_path.exists():
        return 0, 0, [f"File not found: {target_path}"]

    total_count = 0
    valid_count = 0
    all_errors: list[str] = []

    with open(target_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            stripped = line.strip()
            if not stripped:
                continue
            total_count += 1
            try:
                raw_data = json.loads(stripped)
                trace = TrajectoryTrace.model_validate(raw_data)
                errs = validate_trajectory(trace)
                if errs:
                    all_errors.append(f"Line {line_num} (run_id={trace.run_id}): {'; '.join(errs)}")
                else:
                    valid_count += 1
            except (json.JSONDecodeError, pydantic.ValidationError, ValueError, KeyError) as e:
                all_errors.append(f"Line {line_num}: Malformed JSON/schema: {e}")

    return total_count, valid_count, all_errors
