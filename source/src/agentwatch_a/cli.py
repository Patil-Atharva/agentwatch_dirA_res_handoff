"""Command Line Interface for AgentWatch-A.

Adheres to Section 13.2 of AGENTWATCH_DIRECTION_A_SPEC.md.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from agentwatch_a import __version__
from agentwatch_a.settings import ConfigurationError, Settings

app = typer.Typer(
    name="agentwatch",
    help="AgentWatch-A: Black-box online pre-execution monitor for LLM agents.",
    add_completion=False,
)
console = Console()


@app.command()
def version() -> None:
    """Print AgentWatch-A version."""
    console.print(f"[bold green]AgentWatch-A[/bold green] version: {__version__}")


@app.command()
def doctor() -> None:
    """Run environment, dependencies, and security diagnostics."""
    project_root = Path(__file__).resolve().parent.parent.parent
    doctor_script = project_root / "scripts" / "verify_environment.py"
    if doctor_script.is_file():
        import runpy
        exit_code = runpy.run_path(str(doctor_script)).get("check_environment", lambda: 0)()
        if exit_code != 0:
            sys.exit(exit_code)
    else:
        console.print("[red]Error:[/red] verify_environment.py script not found.")
        sys.exit(1)


@app.command()
def check_config(
    config: Annotated[
        Path,
        typer.Option(
            "--config",
            "-c",
            help="Path to YAML configuration file.",
        ),
    ] = Path("config/default.yaml"),
) -> None:
    """Validate a YAML configuration file against authoritative schema."""
    try:
        settings = Settings.from_yaml(config)
        console.print(f"[green][+][/green] Configuration valid: [bold]{config}[/bold]")
        console.print(f"  Project: {settings.project.name} v{settings.project.version} (Seed: {settings.project.seed})")
        console.print(f"  Primary Model: {settings.monitor.primary_model}")
        console.print(f"  Calibration Method: {settings.calibration.method} (Alpha: {settings.calibration.primary_alpha})")
    except ConfigurationError as e:
        console.print(f"[red][-] Configuration Error:[/red] {e}")
        sys.exit(1)


traces_app = typer.Typer(
    name="traces",
    help="Trace management, inspection, and validation commands.",
)
app.add_typer(traces_app, name="traces")


@traces_app.command("validate")
def validate_traces(
    input_file: Annotated[
        Path,
        typer.Option(
            "--input",
            "-i",
            help="Path to JSONL trace file to validate.",
        ),
    ] = Path("tests/fixtures/tiny_synthetic_traces.jsonl"),
) -> None:
    """Validate a JSONL trace file against causality, isolation, and label invariants."""
    from agentwatch_a.trace_store import validate_trace_file

    total, valid, errors = validate_trace_file(input_file)
    if errors:
        console.print(f"[red][-] Validation FAILED for [bold]{input_file}[/bold][/red]")
        console.print(f"    Valid traces: {valid}/{total}")
        for err in errors[:10]:
            console.print(f"    - {err}")
        if len(errors) > 10:
            console.print(f"    ... and {len(errors) - 10} more errors")
        sys.exit(1)
    else:
        console.print(f"[green][+][/green] Validation PASSED for [bold]{input_file}[/bold]")
        console.print(f"    All {valid}/{total} traces strictly conform to Section 6.1 and Appendix A.")


if __name__ == "__main__":
    app()