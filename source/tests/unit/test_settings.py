"""Unit tests for configuration loading and validation."""

from pathlib import Path

import pytest

from agentwatch_a.settings import ConfigurationError, Settings


def test_default_config_loads_valid():
    config_file = Path("config/default.yaml")
    settings = Settings.from_yaml(config_file)
    assert settings.project.name == "agentwatch-a"
    assert settings.project.version == "0.1.0"
    assert settings.project.seed == 17
    assert settings.monitor.primary_model == "goal_conditioned_gru"
    assert settings.calibration.primary_alpha == 0.05
    assert settings.monitor.use_thought_text is False


def test_path_resolution(tmp_path: Path):
    settings = Settings()
    resolved = settings.paths.resolve_paths(tmp_path)
    assert resolved.raw_data == (tmp_path / "data/raw").resolve()
    assert resolved.runs == (tmp_path / "runs").resolve()


def test_missing_config_raises_error(tmp_path: Path):
    non_existent = tmp_path / "does_not_exist.yaml"
    with pytest.raises(ConfigurationError, match="Configuration file not found"):
        Settings.from_yaml(non_existent)


def test_malformed_yaml_raises_error(tmp_path: Path):
    bad_yaml = tmp_path / "bad.yaml"
    bad_yaml.write_text("project: [unclosed_list", encoding="utf-8")
    with pytest.raises(ConfigurationError, match="Failed to parse YAML"):
        Settings.from_yaml(bad_yaml)


def test_extra_field_forbidden_raises_error(tmp_path: Path):
    invalid_config = tmp_path / "invalid_project.yaml"
    invalid_config.write_text("project:\n  extra_forbidden_key: 123\n", encoding="utf-8")
    with pytest.raises(ConfigurationError, match="validation failed"):
        Settings.from_yaml(invalid_config)