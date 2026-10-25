"""Configuration system for AgentWatch-A.

Loads and validates experiment, benchmark, model, and evaluation configurations.
Adheres to Section 16.1 of AGENTWATCH_DIRECTION_A_SPEC.md.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError


class ConfigurationError(Exception):
    """Raised when configuration is invalid, missing, or malformed."""


class ProjectConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = "agentwatch-a"
    version: str = "0.1.0"
    seed: int = 17


class PathsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    raw_data: Path = Path("./data/raw")
    processed_data: Path = Path("./data/processed")
    splits: Path = Path("./data/splits")
    runs: Path = Path("./runs")
    reports: Path = Path("./reports")

    def resolve_paths(self, root: Path) -> PathsConfig:
        """Resolve relative paths against given project root."""
        return PathsConfig(
            raw_data=(root / self.raw_data).resolve(),
            processed_data=(root / self.processed_data).resolve(),
            splits=(root / self.splits).resolve(),
            runs=(root / self.runs).resolve(),
            reports=(root / self.reports).resolve(),
        )


class BenchmarkConfig(BaseModel):
    model_config = ConfigDict(extra="allow")
    name: str = "agentdojo"
    package_version: str | None = None
    repository_commit: str | None = None
    task_revision: str | None = None
    suites: list[str] = Field(default_factory=lambda: ["workspace"])
    attack_levels: list[str] = Field(default_factory=lambda: ["L0"])


class MonitorConfig(BaseModel):
    model_config = ConfigDict(extra="allow")
    mode: str = "detect_only"
    primary_model: str = "goal_conditioned_gru"
    use_thought_text: bool = False
    use_provenance: bool = False
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    chunk_pooling: str = "max"
    max_observation_tokens: int = 512


class CalibrationConfig(BaseModel):
    model_config = ConfigDict(extra="allow")
    method: str = "split_conformal_max_score"
    primary_alpha: float = 0.05
    secondary_alpha: float = 0.01
    score_normalization: str = "raw"


class SplitsConfig(BaseModel):
    model_config = ConfigDict(extra="allow")
    group_key: str = "user_task_id"
    hold_out_attack_templates: bool = True
    hold_out_agent_for_cross_agent_test: bool = True
    external_ood_benchmark: str | None = "agentdyn"


class ReproducibilityConfig(BaseModel):
    model_config = ConfigDict(extra="allow")
    learned_model_seeds: list[int] = Field(default_factory=lambda: [17, 29, 43])
    save_raw_scores: bool = True
    save_split_ids: bool = True
    save_code_commit: bool = True
    save_environment_manifest: bool = True


class Settings(BaseModel):
    """Authoritative settings container for AgentWatch-A."""
    model_config = ConfigDict(extra="allow")

    project: ProjectConfig = Field(default_factory=ProjectConfig)
    paths: PathsConfig = Field(default_factory=PathsConfig)
    benchmark: BenchmarkConfig = Field(default_factory=BenchmarkConfig)
    monitor: MonitorConfig = Field(default_factory=MonitorConfig)
    calibration: CalibrationConfig = Field(default_factory=CalibrationConfig)
    splits: SplitsConfig = Field(default_factory=SplitsConfig)
    reproducibility: ReproducibilityConfig = Field(default_factory=ReproducibilityConfig)

    @classmethod
    def from_yaml(cls, path: str | Path, project_root: Path | None = None) -> Settings:
        """Load and validate settings from a YAML configuration file."""
        config_path = Path(path)
        if not config_path.is_file():
            raise ConfigurationError(f"Configuration file not found: {config_path}")

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                raw_data = yaml.safe_load(f) or {}
        except Exception as e:
            raise ConfigurationError(f"Failed to parse YAML from {config_path}: {e}") from e

        try:
            settings = cls(**raw_data)
        except ValidationError as e:
            raise ConfigurationError(f"Configuration validation failed for {config_path}:\n{e}") from e

        if project_root is not None:
            settings.paths = settings.paths.resolve_paths(project_root)

        return settings

