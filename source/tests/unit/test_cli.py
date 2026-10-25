"""Unit tests for AgentWatch-A CLI."""

from pathlib import Path

from typer.testing import CliRunner

from agentwatch_a.cli import app

runner = CliRunner()


def test_cli_version():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_cli_check_config():
    result = runner.invoke(app, ["check-config", "--config", "config/default.yaml"])
    assert result.exit_code == 0
    assert "Configuration valid" in result.output


def test_cli_check_config_nonexistent(tmp_path: Path):
    bad_path = str(tmp_path / "missing.yaml")
    result = runner.invoke(app, ["check-config", "--config", bad_path])
    assert result.exit_code != 0