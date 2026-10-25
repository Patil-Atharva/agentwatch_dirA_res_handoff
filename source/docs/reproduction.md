# Reproducibility Guide

Adheres to Section 16 and Section 20.3 of AGENTWATCH_DIRECTION_A_SPEC.md.

## Deterministic Execution
1. Virtual environment: Python 3.11 with `requirements.lock`.
2. Seeds: Fixed random seeds configured in YAML (`default.yaml`).
3. Splits: Task-disjoint splits stored as immutable JSON lists in `data/splits/`.
4. Run Manifests: Every experiment generates an immutable directory under `runs/<run_id>/` containing resolved configs, git commit SHA, environment details, and raw score logs.