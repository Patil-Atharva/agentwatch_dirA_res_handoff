"""Environment verification and diagnostic tool for AgentWatch-A (agentwatch doctor).

Adheres to Section 14.10 of AGENTWATCH_DIRECTION_A_SPEC.md.
Never prints or logs secret values.
"""

from __future__ import annotations

import os
import platform
import sys
from pathlib import Path


def check_environment() -> int:
    print("=" * 60)
    print("AgentWatch-A: Environment Doctor & Diagnostic Check")
    print("=" * 60)

    project_root = Path(__file__).resolve().parent.parent
    errors: list[str] = []
    warnings: list[str] = []

    # 1. Python version and executable
    py_version = sys.version_info
    py_ver_str = f"{py_version.major}.{py_version.minor}.{py_version.micro}"
    print(f"[x] Python Version: {py_ver_str}")
    print(f"[x] Python Executable: {sys.executable}")

    if py_version.major != 3 or py_version.minor != 11:
        errors.append(f"Incompatible Python version: {py_ver_str}. Python 3.11 is required.")

    # Check if running inside .venv
    in_venv = sys.prefix != sys.base_prefix
    print(f"[x] Virtual Environment Active: {in_venv} (Prefix: {sys.prefix})")
    if not in_venv:
        warnings.append("Not running inside a virtual environment (.venv).")

    # 2. OS and Architecture
    print(f"[x] OS Platform: {platform.system()} {platform.release()} ({platform.machine()})")

    # 3. Project Root & Core Files
    print(f"[x] Project Root: {project_root}")
    required_files = [
        "AGENTWATCH_DIRECTION_A_SPEC.md",
        "AGENTS.md",
        "pyproject.toml",
        ".gitignore",
        ".env.example",
    ]
    for filename in required_files:
        filepath = project_root / filename
        exists = filepath.is_file()
        status = "FOUND" if exists else "MISSING"
        print(f"    - {filename}: {status}")
        if not exists:
            errors.append(f"Required project file missing: {filename}")

    # 4. Check .gitignore integrity
    gitignore_path = project_root / ".gitignore"
    if gitignore_path.is_file():
        gitignore_content = gitignore_path.read_text(encoding="utf-8")
        essential_patterns = [".venv", ".env", "/data/raw/**", "/runs/"]
        for pat in essential_patterns:
            if pat not in gitignore_content:
                warnings.append(f"Pattern '{pat}' not explicitly found in .gitignore.")

    # 5. Output directories writability
    data_dirs = ["data", "runs", "reports"]
    for dir_name in data_dirs:
        dir_path = project_root / dir_name
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            test_file = dir_path / ".write_test"
            test_file.write_text("ok", encoding="utf-8")
            test_file.unlink()
            print(f"[x] Directory '{dir_name}': Exists and Writable")
        except OSError as e:
            errors.append(f"Directory '{dir_name}' not writable: {e}")

    # 6. Check PyTorch & GPU
    try:
        import torch

        cuda_available = torch.cuda.is_available()
        cuda_device = torch.cuda.get_device_name(0) if cuda_available else "None"
        print(f"[x] PyTorch: Installed ({torch.__version__}), CUDA Available: {cuda_available} ({cuda_device})")
    except ImportError:
        print("[!] PyTorch: Not installed yet")

    # 7. Check Core ML / Data Packages
    packages = ["pydantic", "pytest", "ruff", "numpy", "yaml"]
    for pkg in packages:
        try:
            __import__(pkg)
            print(f"[x] Package '{pkg}': Installed")
        except ImportError:
            print(f"[!] Package '{pkg}': Not installed yet")

    # 8. Environment variables status (NEVER print values)
    api_keys = ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY", "HF_TOKEN"]
    print("[x] Environment Keys Status:")
    for key in api_keys:
        is_set = bool(os.environ.get(key))
        print(f"    - {key}: {'CONFIGURED' if is_set else 'NOT SET'}")

    # Summary
    print("-" * 60)
    if warnings:
        print(f"WARNINGS ({len(warnings)}):")
        for w in warnings:
            print(f"  [!] {w}")
    if errors:
        print(f"ERRORS ({len(errors)}):")
        for err in errors:
            print(f"  [X] {err}")
        print("Doctor check: FAILED")
        return 1

    print("Doctor check: PASSED (Core environment verified)")
    return 0


if __name__ == "__main__":
    sys.exit(check_environment())
