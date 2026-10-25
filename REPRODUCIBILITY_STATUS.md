# AgentWatch-A: Reproducibility Status & Audit

**Audit Date**: 2026-10-25  
**Master Runner**: [`scripts/reproduce_all.py`](source/scripts/reproduce_all.py)  

---

## 1. Reproduction Verification Summary

The master reproduction pipeline was executed in 4 independent Python processes on consumer x86_64 Windows CPU:
- **Elapsed Time**: **$3.89\text{ seconds}$**.
- **Stage 1 (Environment Audit)**: Python 3.11.0, PyTorch 2.14.1+cpu, AgentDojo 0.1.35 (MIT License) validated.
- **Stage 2 (Trace Integrity)**: 20/20 canonical traces verified against SHA-256 cryptographic hashes.
- **Stage 3 (Baseline Fitting)**: B1, B3, B4, B6 fitted deterministically (`torch.manual_seed(42)`).
- **Stage 4 (Monitor Checkpoint)**: `data/goal_conditioned_gru.pt` loaded and cosine projection validated.
- **Stage 5 (Conformal Calibration)**: Order statistic $\hat{\tau} = 0.551474$ replicated bit-exactly.
- **Stage 6 (Track 1 & Track 2 Evaluation)**: All metrics reproduced with **0 discrepancies**.
- **Stage 7 (Registry Assertion)**: Audited all outputs against `data/result_registry.json`.

---

## 2. Determinism and Environment Control

- **CRC32 Determinism**: Python's built-in `hash()` randomized by `PYTHONHASHSEED` was replaced with deterministic `zlib.crc32(word.encode()) % 10000`, ensuring cross-platform, cross-process bit-exact representations.
- **Zero Cloud API Dependencies**: The entire pipeline executes locally without external LLM API calls, preventing provider drift or billing costs.

---

## 3. Reproduction Command

To reproduce all 7 validation stages from clean source:
```bash
python scripts/reproduce_all.py
```
To run the full unit and integration test suite:
```bash
pytest -v
```
All 60 tests execute in < 25 seconds.
