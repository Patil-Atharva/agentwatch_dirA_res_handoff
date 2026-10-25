"""Deterministic argument provenance and taint tracking utilities.

Adheres strictly to Section 8.7 of AGENTWATCH_DIRECTION_A_SPEC.md.
"""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from agentwatch_a.models.interface import PreExecutionInput

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
URL_REGEX = re.compile(r"https?://\S+")
PATH_REGEX = re.compile(r"(?:/[a-zA-Z0-9_.-]+)+|[a-zA-Z]:\\[a-zA-Z0-9_.\\]+")

HIGH_IMPACT_TOOLS: set[str] = {
    "send_email",
    "delete_email",
    "delete_file",
    "share_file",
    "cancel_calendar_event",
    "reschedule_calendar_event",
    "append_to_file",
    "create_file",
}

UNTRUSTED_TOOLS: set[str] = {
    "get_unread_emails",
    "get_received_emails",
    "search_emails",
    "search_calendar_events",
    "search_files",
    "get_file_by_id",
    "list_files",
}


class ProvenanceFeatureSet(BaseModel):
    """Deterministic provenance and risk features for a proposed action."""
    model_config = ConfigDict(extra="forbid")

    high_impact_tool: bool = Field(default=False, description="Whether proposed tool is high impact")
    high_impact_untrusted_argument: bool = Field(
        default=False,
        description="Whether high-impact tool takes argument first seen in untrusted observation",
    )
    num_arguments: int = Field(default=0, description="Total number of primitive string argument values")
    num_arguments_in_goal: int = Field(default=0, description="Number of argument values appearing in user goal")
    num_arguments_from_untrusted: int = Field(
        default=0,
        description="Number of argument values appearing in untrusted observations",
    )
    detected_entities: list[str] = Field(
        default_factory=list,
        description="List of detected entity types (email, url, path)",
    )
    argument_provenance_details: dict[str, Any] = Field(
        default_factory=dict,
        description="Per-argument provenance lookup table",
    )


def detect_entity_type(val: str) -> str:
    """Classify string value into entity type (email, url, path, or other)."""
    if EMAIL_REGEX.search(val):
        return "email"
    if URL_REGEX.search(val):
        return "url"
    if PATH_REGEX.search(val):
        return "path"
    return "other"


def _flatten_arg_strings(args: Any) -> list[tuple[str, str]]:
    """Flatten dictionary or list of arguments into list of (key_path, string_value)."""
    result: list[tuple[str, str]] = []
    if isinstance(args, dict):
        for k, v in args.items():
            if isinstance(v, str):
                result.append((str(k), v))
            elif isinstance(v, (list, tuple)):
                for idx, item in enumerate(v):
                    if isinstance(item, str):
                        result.append((f"{k}[{idx}]", item))
                    elif isinstance(item, dict):
                        for sub_k, sub_v in _flatten_arg_strings(item):
                            result.append((f"{k}[{idx}].{sub_k}", sub_v))
            elif isinstance(v, dict):
                for sub_k, sub_v in _flatten_arg_strings(v):
                    result.append((f"{k}.{sub_k}", sub_v))
    return result


def extract_provenance_features(input_event: PreExecutionInput) -> ProvenanceFeatureSet:
    """Extract deterministic argument provenance features from PreExecutionInput."""
    proposed_tool = input_event.proposed_tool
    is_high_impact = proposed_tool in HIGH_IMPACT_TOOLS

    norm_goal = " ".join(input_event.goal.lower().split())

    # Build untrusted text corpus from prior observations
    untrusted_corpus = ""
    for idx, act in enumerate(input_event.prior_actions):
        t_name = act.get("tool", "")
        if t_name in UNTRUSTED_TOOLS and idx < len(input_event.prior_observations):
            untrusted_corpus += " " + input_event.prior_observations[idx]

    norm_untrusted = " ".join(untrusted_corpus.lower().split())

    flattened_args = _flatten_arg_strings(input_event.proposed_args)

    num_args = len(flattened_args)
    in_goal_count = 0
    from_untrusted_count = 0
    entities: list[str] = []
    details: dict[str, Any] = {}
    high_impact_untrusted = False

    for key_path, val in flattened_args:
        clean_val = val.strip()
        if len(clean_val) < 3:
            continue

        norm_val = " ".join(clean_val.lower().split())
        in_goal = norm_val in norm_goal
        in_untrusted = norm_val in norm_untrusted
        ent_type = detect_entity_type(clean_val)
        if ent_type != "other" and ent_type not in entities:
            entities.append(ent_type)

        if in_goal:
            in_goal_count += 1
        if in_untrusted and not in_goal:
            from_untrusted_count += 1
            if is_high_impact:
                high_impact_untrusted = True

        details[key_path] = {
            "value_preview": clean_val[:40],
            "in_goal": in_goal,
            "in_untrusted_obs": in_untrusted,
            "entity_type": ent_type,
        }

    return ProvenanceFeatureSet(
        high_impact_tool=is_high_impact,
        high_impact_untrusted_argument=high_impact_untrusted,
        num_arguments=num_args,
        num_arguments_in_goal=in_goal_count,
        num_arguments_from_untrusted=from_untrusted_count,
        detected_entities=entities,
        argument_provenance_details=details,
    )
