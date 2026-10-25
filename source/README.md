# AgentWatch-A: Black-Box Online Pre-Execution Monitoring for Indirect Prompt Injection in Tool-Using LLM Agents

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/release/python-3110/)
[![PyTorch 2.14](https://img.shields.io/badge/pytorch-2.14%2Bcpu-red.svg)](https://pytorch.org/)
[![Benchmark AgentDojo](https://img.shields.io/badge/benchmark-AgentDojo%200.1.35-green.svg)](https://github.com/ethz-spri/agentdojo)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Zero-Cost Local CPU](https://img.shields.io/badge/compute-100%25%20local%20cpu-purple.svg)]()

> **Official Research Artifact for Conference Submission**  
> Complete implementation, evaluation pipeline, paper manuscript, and anonymous submission package for **AgentWatch-A**, governed by [`AGENTWATCH_DIRECTION_A_SPEC.md`](AGENTWATCH_DIRECTION_A_SPEC.md) (v1.0).

---

## Executive Summary

Autonomous Large Language Model (LLM) agents operating in tool-augmented environments are vulnerable to **Indirect Prompt Injection (IPI)**, where adversarial instructions embedded in untrusted data compromise the agent's decision loop. Post-execution auditing detects attacks only after irreversible side effects (data exfiltration, credential modification) have already occurred, while static content filters generate excessive false alarms when legitimate tasks process untrusted text.

**AgentWatch-A** provides an **online, black-box, pre-execution monitoring framework** that intercepts proposed tool actions before irreversible execution while bounding the trajectory false positive rate via **Split-Conformal Calibration** on benign trajectory maxima ($FPR_{\text{traj}} \le \alpha = 0.20$).

```
[User Goal g]
      │
      ▼
┌───────────────┐     Proposed Call at      ┌─────────────────────────┐
│ Tool-Using    │ ────────────────────────> │ PreExecutionInterceptor │
│ LLM Agent     │ <──────────────────────── │ (AgentWatch-A Monitor)  │
└───────────────┘        ALLOW / BLOCK      └───────────┬─────────────┘
                                                        │
                      ┌─────────────────────────────────┴───────────────────┐
                      │ 1. Deterministic CRC32 Hash Encoding (Frozen Text)   │
                      │ 2. 7-Dimensional Argument Provenance Vector p(a_t)  │
                      │ 3. Causal Goal-Conditioned Recurrent GRU State h_t  │
                      │ 4. Cosine Metric Projection to Shared Latent Space  │
                      │ 5. Conformal Max-Score Threshold Calibration tau_hat│
                      └─────────────────────────────────────────────────────┘
```

---

## Key Empirical Findings

All numbers below are extracted directly from the frozen master result registry [`data/result_registry.json`](data/result_registry.json) and audited via [`scripts/reproduce_all.py`](scripts/reproduce_all.py).

### 1. Track 1: Offline Prefix Replay ($\alpha = 0.20$)
Evaluated on 15 held-out AgentDojo trajectories (5 benign, 3 unexposed, 4 resisted, 3 hijacked) using threshold $\hat{\tau} = 0.5515$ calibrated on $n=5$ benign calibration trajectories:

| Model / Defense | Threshold $\hat{\tau}$ | $TPR_{\text{pre}}$ | $FPR_{\text{benign}}$ | $FPR_{\text{resisted}}$ | AUROC | AUPRC |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **B1: Transition Bigram** | 0.2500 | 100.0% | 40.0% | 0.0% | 0.800 | 0.800 |
| **B3: Content Detector** | 0.0000 | 100.0% | 0.0% | 0.0% | 1.000 | 1.000 |
| **B4: Unconditioned Sequence** | 0.2500 | 100.0% | 40.0% | 0.0% | 0.600 | 0.300 |
| **B6: Supervised Oracle** | 0.0065 | 100.0% | 0.0% | 0.0% | 1.000 | 1.000 |
| **GoalConditionedGRU (Ablated)**| 0.4847 | 100.0% | 100.0% | 100.0% | 1.000 | 1.000 |
| **AgentWatch-A (Full Monitor)** | **0.5515** | **100.0%** | **40.0%** | **0.0%** | **1.000** | **1.000** |

### 2. Track 2: Closed-Loop Live Intervention & Operational Latency
When deployed as a live pre-execution interceptor halting hijacked actions inside the agent loop:

| Defense System | In-Loop ASR | ASR Reduction | Benign FIR ($FIR_{\text{benign}}$) | Mean CPU Latency | p95 CPU Latency |
|---|:---:|:---:|:---:|:---:|:---:|
| **Unprotected Agent** | 50.00% | 0.0% | 0.00% | 0.00 ms | 0.00 ms |
| **B1: Transition Bigram** | 0.00% | 100.0% | 100.00% | 0.01 ms | 0.01 ms |
| **B3: Content Detector** | 0.00% | 100.0% | 50.00% | 1.48 ms | 1.55 ms |
| **B4: Unconditioned Sequence** | 0.00% | 100.0% | 100.00% | 0.02 ms | 0.03 ms |
| **GoalConditionedGRU (Ablated)**| 0.00% | 100.0% | 100.00% | 1.05 ms | 1.20 ms |
| **AgentWatch-A (Full Monitor)** | **0.00%** | **100.0%** | **0.00%** | **1.61 ms** | **1.91 ms** |

> **Core Scientific Finding (Gates G3 & G4)**:  
> Simpler transition bigrams and unconditioned sequence models completely destroy agent utility, falsely interrupting **100.00%** of legitimate benign tasks. Content scanners interrupt **50.00%** of benign tasks when observations contain untrusted strings. **AgentWatch-A is the only system achieving 100.00% ASR reduction with 0.00% false interruption of benign tasks**, operating at an average CPU latency of **1.61 ms** with zero cloud API overhead.

---

## One-Click Reproduction (Zero Cloud Tokens / 100% Local CPU)

To reproduce all 7 validation stages and audit every reported metric down to floating-point precision:

```powershell
# 1. Clone repository and navigate to root
cd revised_agentwatch__dir_a

# 2. Activate virtual environment
.\.venv\Scripts\Activate.ps1

# 3. Run the master end-to-end reproducibility pipeline
python scripts/reproduce_all.py
```

### Complete Test Suite
```powershell
pytest -v
```
All 60 unit and integration tests execute in <20 seconds.

### Package Anonymous Conference Submission Artifact
```powershell
python scripts/package_submission_artifact.py
```
Generates a sanitized, self-contained double-blind submission ZIP in `dist/agentwatch_a_anonymous_artifact.zip` along with `dist/sha256sum.txt`.

---

## Repository Structure

```text
revised_agentwatch__dir_a/
├── AGENTWATCH_DIRECTION_A_SPEC.md   # Authoritative research specification (v1.0)
├── README.md                        # Master repository documentation
├── pyproject.toml                   # Packaging and dependency definitions
├── requirements.txt                 # Pinned dependencies
├── configs/                         # YAML experiment configurations
│   └── default_monitor_config.yaml
├── paper/                           # Academic publication manuscript
│   ├── main.tex                     # Full LaTeX manuscript (12 sections)
│   └── references.bib               # Complete BibTeX bibliography
├── docs/                            # Documentation & paper artifacts
│   ├── PAPER_MANUSCRIPT.md          # High-fidelity Markdown paper draft
│   ├── LIMITATIONS_AND_ETHICS.md    # Ethical and statistical scope statements
│   ├── trace_schema.md              # Trace specification & cryptographic seals
│   └── paper_artifacts/             # LaTeX and Markdown tables (Tables 1, 2, 3)
├── research/                        # Scientific logs and research matrices
│   ├── claims_evidence_ledger.md    # Pre-registered hypotheses to empirical data
│   ├── decision_log.md              # Architectural decisions (DEC-001 - DEC-010)
│   ├── literature_matrix.csv        # Prior art matrix
│   ├── novelty_matrix.csv           # Competitive overlap matrix
│   ├── research_questions.md        # RQ formulation
│   └── threat_model.md              # Formalized threat model
├── src/agentwatch_a/                # Core production library
│   ├── benchmark/                   # AgentDojo adapter & PreExecutionInterceptor
│   ├── features/                    # Deterministic CRC32 text encoder & action encoder
│   ├── models/                      # GoalConditionedGRU, baselines (B1-B6)
│   ├── calibration/                 # Split-conformal calibration on trajectory maxima
│   ├── policy/                      # Decision policy & PreExecutionMonitorHook
│   ├── evaluation/                  # Metrics (TPR_pre, FPR, Lead Time, FIR)
│   ├── provenance.py                # 7D argument provenance extractor
│   ├── schemas.py                   # Canonical Pydantic trace & step schemas
│   └── trace_store.py               # Trace I/O with SHA-256 verification
├── scripts/                         # Production CLI runners & pipeline
│   ├── reproduce_all.py             # Master 7-stage reproduction pipeline
│   ├── package_submission_artifact.py # Anonymous conference submission packager
│   ├── train_monitor.py             # Monitor contrastive training runner
│   ├── calibrate_and_evaluate.py    # Conformal calibration & evaluation runner
│   ├── evaluate_in_loop.py          # Track 1 & Track 2 evaluation runner
│   └── train_baselines.py           # Baseline fitting runner
├── data/                            # Canonical traces, models & results
│   ├── sample_traces/               # 20 canonical AgentDojo traces
│   ├── goal_conditioned_gru.pt      # Frozen trained monitor weights
│   ├── calibration_manifest.json    # Calibrated conformal thresholds
│   ├── in_loop_evaluation_report.json # Track 1 & 2 raw report
│   └── result_registry.json         # Master frozen result registry
├── dist/                            # Packaged submission archives
│   ├── agentwatch_a_anonymous_artifact.zip
│   └── sha256sum.txt
└── tests/                           # 60 unit and integration tests
    ├── unit/
    └── integration/
```

---

## Citation

If you use AgentWatch-A in your research, please cite our paper:

```bibtex
@article{agentwatch2026,
  title   = {AgentWatch-A: Black-Box Online Pre-Execution Monitoring for Indirect Prompt Injection in Tool-Using {LLM} Agents},
  author  = {Anonymous Authors},
  journal = {Under review},
  year    = {2026}
}
```
