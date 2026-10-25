"""Benchmark version and environment verification module for AgentDojo.

Adheres to Section 10.1 and Phase 3 of AGENTWATCH_DIRECTION_A_SPEC.md.
"""

from __future__ import annotations

import importlib.metadata
import json
import urllib.request

from pydantic import BaseModel, ConfigDict


class BenchmarkAuditReport(BaseModel):
    """Structured audit report for benchmark environment and dependencies."""
    model_config = ConfigDict(extra="forbid")

    agentdojo_installed: bool
    agentdojo_version: str | None = None
    agentdojo_license: str = "MIT"
    supported_benchmark_versions: list[str] = []
    default_suite: str = "workspace"
    user_tasks_count: int = 0
    injection_tasks_count: int = 0
    ollama_online: bool = False
    ollama_models: list[str] = []
    ready_for_benchmarking: bool = False
    issues: list[str] = []


def audit_benchmark_environment(
    benchmark_version: str = "v1",
    suite_name: str = "workspace",
    ollama_host: str = "http://127.0.0.1:11434",
) -> BenchmarkAuditReport:
    """Audit AgentDojo package version, suite availability, and local Ollama endpoint."""
    issues: list[str] = []

    # 1. AgentDojo package check
    try:
        pkg_version = importlib.metadata.version("agentdojo")
        agentdojo_installed = True
    except importlib.metadata.PackageNotFoundError:
        pkg_version = None
        agentdojo_installed = False
        issues.append("agentdojo package is not installed in the active environment.")

    # 2. Inspect available suites and versions
    supported_versions: list[str] = []
    user_tasks_count = 0
    injection_tasks_count = 0

    if agentdojo_installed:
        try:
            from agentdojo.task_suite.load_suites import _SUITES, get_suite

            supported_versions = list(_SUITES.keys())
            if benchmark_version in _SUITES and suite_name in _SUITES[benchmark_version]:
                suite = get_suite(benchmark_version, suite_name)
                user_tasks_count = len(suite.user_tasks)
                injection_tasks_count = len(suite.injection_tasks)
            else:
                issues.append(f"Suite '{suite_name}' not found under version '{benchmark_version}'.")
        except Exception as e:  # noqa: BLE001 - third-party dynamic suite loader may raise unexpected exceptions
            issues.append(f"Failed to load AgentDojo suite '{suite_name}': {e}")

    # 3. Check local Ollama endpoint
    ollama_online = False
    ollama_models: list[str] = []
    try:
        req = urllib.request.Request(f"{ollama_host}/api/tags", headers={"User-Agent": "AgentWatch-A"})
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                ollama_online = True
                ollama_models = [m.get("name", "") for m in data.get("models", [])]
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as e:
        issues.append(f"Ollama daemon not reachable at {ollama_host}: {e}")

    ready = agentdojo_installed and user_tasks_count > 0 and len(issues) == 0

    return BenchmarkAuditReport(
        agentdojo_installed=agentdojo_installed,
        agentdojo_version=pkg_version,
        agentdojo_license="MIT",
        supported_benchmark_versions=supported_versions,
        default_suite=suite_name,
        user_tasks_count=user_tasks_count,
        injection_tasks_count=injection_tasks_count,
        ollama_online=ollama_online,
        ollama_models=ollama_models,
        ready_for_benchmarking=ready,
        issues=issues,
    )

