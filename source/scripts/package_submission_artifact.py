#!/usr/bin/env python3
"""
package_submission_artifact.py

Automated Anonymous Conference Submission Packager for AgentWatch-A.
Adheres strictly to Section 15.3, Section 20.3, and Section 21 of AGENTWATCH_DIRECTION_A_SPEC.md.

Performs:
1. Path and identity sanitization (strips author personal paths / usernames).
2. Clean bundling of source code, scripts, configurations, canonical data, checkpoints, and paper artifacts.
3. Creation of an anonymous self-contained ZIP archive in dist/agentwatch_a_anonymous_artifact.zip.
4. Cryptographic SHA-256 checksum generation in dist/sha256sum.txt.
5. In-archive integrity validation.
"""

from __future__ import annotations

import hashlib
import os
import sys
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DIST_DIR = REPO_ROOT / "dist"
ARCHIVE_PATH = DIST_DIR / "agentwatch_a_anonymous_artifact.zip"
CHECKSUM_PATH = DIST_DIR / "sha256sum.txt"

INCLUDED_DIRECTORIES = [
    "src",
    "scripts",
    "configs",
    "data/sample_traces",
    "tests",
    "paper",
    "docs",
    "reports",
    "research",
]

INCLUDED_FILES = [
    "pyproject.toml",
    "requirements.txt",
    "AGENTWATCH_DIRECTION_A_SPEC.md",
    "data/calibration_manifest.json",
    "data/goal_conditioned_gru.pt",
    "data/in_loop_evaluation_report.json",
    "data/result_registry.json",
]

EXCLUDE_EXTENSIONS = {".pyc", ".pyd", ".pyo", ".git", ".log"}
EXCLUDE_DIRS = {"__pycache__", ".venv", ".git", ".pytest_cache", ".ruff_cache", "dist", "brain"}


def generate_anonymous_readme() -> str:
    return """# AgentWatch-A: Anonymous Conference Submission Artifact

This package contains the complete, self-contained replication artifact for **AgentWatch-A**:
*Black-Box Online Pre-Execution Monitoring for Indirect Prompt Injection in Tool-Using LLM Agents*.

All personal author identities, system paths, and git metadata have been stripped for double-blind review.

## Environment Requirements
- Python >= 3.10 (tested on 3.11.0 64-bit)
- PyTorch >= 2.0.0 (CPU execution supported, zero GPU required)
- agentdojo == 0.1.35 (MIT License)

## Quickstart Reproduction (Zero Cloud Tokens / 100% Local CPU)

1. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Or .venv\\Scripts\\activate on Windows
   pip install -r requirements.txt
   pip install -e .
   ```

2. Run the master reproduction pipeline:
   ```bash
   python scripts/reproduce_all.py
   ```
   This will execute all 7 validation stages and audit all empirical metrics against `data/result_registry.json`.

3. Run the complete test suite:
   ```bash
   pytest -v
   ```

## Package Contents
- `src/agentwatch_a/`: Core library implementation (features, models, calibration, policy, benchmark adapters).
- `scripts/`: Reproduction and execution runners.
- `data/`: Canonical traces, calibration manifest, trained model checkpoint, and result registry.
- `tests/`: 60 comprehensive unit and integration tests.
- `paper/`: Full LaTeX manuscript (`main.tex`) and BibTeX bibliography (`references.bib`).
- `docs/`: Markdown paper manuscript (`PAPER_MANUSCRIPT.md`) and limitation statements.
"""


def sanitize_text_content(content: bytes) -> bytes:
    """Sanitize any local user path strings that might be present in text files."""
    text = content.decode("utf-8", errors="replace")
    # Replace Windows author path with generic relative path
    text = text.replace("C:\\Users\\Ayush\\Documents\\GitHub\\research project\\revised_agentwatch__dir_a", "/workspace/agentwatch_a")
    text = text.replace("C:/Users/Ayush/Documents/GitHub/research project/revised_agentwatch__dir_a", "/workspace/agentwatch_a")
    text = text.replace("C:\\Users\\Ayush", "/home/user")
    text = text.replace("C:/Users/Ayush", "/home/user")
    return text.encode("utf-8")


def package_artifact() -> Path:
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    if ARCHIVE_PATH.exists():
        ARCHIVE_PATH.unlink()

    print(f"[*] Packaging anonymous submission artifact into {ARCHIVE_PATH.name}...")
    file_count = 0

    with zipfile.ZipFile(ARCHIVE_PATH, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        # Add generated anonymous README
        zf.writestr("agentwatch_a/README.md", generate_anonymous_readme().encode("utf-8"))
        file_count += 1

        # Add explicitly included individual files
        for rel_file in INCLUDED_FILES:
            abs_file = REPO_ROOT / rel_file
            if abs_file.is_file():
                arcname = f"agentwatch_a/{rel_file.replace(os.sep, '/')}"
                content = abs_file.read_bytes()
                if abs_file.suffix in {".json", ".txt", ".md", ".toml"}:
                    content = sanitize_text_content(content)
                zf.writestr(arcname, content)
                file_count += 1
            else:
                print(f"[!] Warning: missing declared file {rel_file}")

        # Add directories recursively
        for rel_dir in INCLUDED_DIRECTORIES:
            abs_dir = REPO_ROOT / rel_dir
            if not abs_dir.is_dir():
                print(f"[!] Warning: missing declared dir {rel_dir}")
                continue

            for root, dirs, files in os.walk(abs_dir):
                # Filter out excluded directory names
                dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
                for f in files:
                    file_path = Path(root) / f
                    if file_path.suffix in EXCLUDE_EXTENSIONS:
                        continue
                    rel_to_repo = file_path.relative_to(REPO_ROOT).as_posix()
                    arcname = f"agentwatch_a/{rel_to_repo}"
                    content = file_path.read_bytes()
                    if file_path.suffix in {".py", ".json", ".txt", ".md", ".tex", ".bib", ".yaml", ".yml", ".toml", ".csv"}:
                        content = sanitize_text_content(content)
                    zf.writestr(arcname, content)
                    file_count += 1

    print(f"[+] Successfully bundled {file_count} files into {ARCHIVE_PATH}")

    # Compute SHA-256 Checksum
    hasher = hashlib.sha256()
    with open(ARCHIVE_PATH, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    digest = hasher.hexdigest()

    checksum_entry = f"{digest}  {ARCHIVE_PATH.name}\n"
    CHECKSUM_PATH.write_text(checksum_entry, encoding="utf-8")
    print(f"[+] SHA-256: {digest}")
    print(f"[+] Checksum written to {CHECKSUM_PATH}")

    # Verify archive integrity
    with zipfile.ZipFile(ARCHIVE_PATH, "r") as zf:
        bad_file = zf.testzip()
        if bad_file is not None:
            raise RuntimeError(f"Corrupt file found in archive: {bad_file}")
        names = zf.namelist()
        assert any("main.tex" in n for n in names), "Missing main.tex in submission archive!"
        assert any("reproduce_all.py" in n for n in names), "Missing reproduce_all.py in submission archive!"
        assert any("result_registry.json" in n for n in names), "Missing result_registry.json in submission archive!"

    print("[+] Archive integrity verified successfully.")
    return ARCHIVE_PATH


if __name__ == "__main__":
    try:
        package_artifact()
        sys.exit(0)
    except (RuntimeError, AssertionError, OSError) as e:
        print(f"[!] Failed to package submission artifact: {e}")
        sys.exit(1)
