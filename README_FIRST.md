# AgentWatch-A: Research Evaluation Handoff Package

**Package Name**: `AGENTWATCH_DIRECTION_A_RESEARCH_HANDOFF`  
**Target Audience**: Independent AI Research Scientist / Peer Reviewer / Research Evaluator  
**Source Code Revision**: Git Commit `5d20932`  
**Evidence Cutoff Date**: 2026-10-25  
**Authoritative Specification**: [`AGENTWATCH_DIRECTION_A_SPEC.md`](source/AGENTWATCH_DIRECTION_A_SPEC.md) (v1.0)  

---

## 1. Executive Handoff Overview

Welcome to the independent research evaluation handoff package for **AgentWatch-A**. This package contains the complete, unredacted, evidence-backed record of the AgentWatch-A research initiative.

The primary objective of this project was to resolve a fundamental question in LLM agent security:
> **Core Research Question**: Can an external, black-box, prefix-only runtime monitor detect successful indirect prompt-injection (IPI) hijacks in tool-using LLM agents *before* a harmful tool action executes ($t_{\text{flag}} \le t_{\text{harm}}$), while keeping interruptions to legitimate agent behavior strictly controlled ($FPR_{\text{traj}} \le \alpha = 0.20$)?

---

## 2. Research Scope Resolution (Direction A vs. Direction B)

An essential initial distinction for the evaluator:
- **Direction A (This Repository & Package)**: **Single-Agent Online Pre-Execution Monitoring for Indirect Prompt Injection**.
  - Implemented on the AgentDojo `workspace` benchmark (40 user tasks).
  - Uses a lightweight Goal-Conditioned GRU, deterministic CRC32 feature projection, 7-dimensional argument provenance vector, and split-conformal calibration on benign trajectory maxima.
  - Sits at the tool execution boundary mediated via an active pre-execution hook.
- **Direction B (Multi-Agent Coordination & Protocol Compliance)**: Multi-agent communication, agreement, and behavioral collusion.
  - **Status**: **`OUT OF SCOPE / NOT APPLICABLE`**.
  - **Authoritative Confirmation**: Section 3.2, Line 121 of `AGENTWATCH_DIRECTION_A_SPEC.md` explicitly designates multi-agent security as Direction B and assigns it to another team. Multi-agent metrics are not evaluated in Direction A.

---

## 3. Package Structure and Navigation Guide

| Document | Purpose / Contents |
|---|---|
| [`README_FIRST.md`](README_FIRST.md) | This document: package orientation, scope, and quickstart guide. |
| [`PROJECT_OVERVIEW.md`](PROJECT_OVERVIEW.md) | High-level research context, threat model, intended vs actual design. |
| [`IMPLEMENTATION_MAP.md`](IMPLEMENTATION_MAP.md) | Detailed file-by-file mapping of modules, entry points, and execution control flow. |
| [`IMPLEMENTATION_STATUS_MATRIX.csv`](IMPLEMENTATION_STATUS_MATRIX.csv) | Component-by-component implementation and verification matrix. |
| [`EXPERIMENT_AND_ARTIFACT_REGISTRY.csv`](EXPERIMENT_AND_ARTIFACT_REGISTRY.csv) | Catalog of all experimental conditions, runs, checkpoints, traces, and metrics. |
| [`EXPERIMENTAL_RESULTS_CATALOG.md`](EXPERIMENTAL_RESULTS_CATALOG.md) | Comprehensive quantitative results across Track 1 (Offline Replay) and Track 2 (Live In-Loop). |
| [`TRACE_AND_OBSERVABILITY_FINDINGS.md`](TRACE_AND_OBSERVABILITY_FINDINGS.md) | Trace audit, SHA-256 integrity, temporal isolation, and 3 representative episode reconstructions. |
| [`METRIC_DICTIONARY.md`](METRIC_DICTIONARY.md) | Exact mathematical formulations, numerators, denominators, and censoring rules for all metrics. |
| [`HYPOTHESIS_EVIDENCE_MATRIX.csv`](HYPOTHESIS_EVIDENCE_MATRIX.csv) | Status of pre-registered hypotheses H1–H7 mapped to empirical evidence. |
| [`CLAIMS_EVIDENCE_LEDGER.csv`](CLAIMS_EVIDENCE_LEDGER.csv) | Claims CLAIM-01 to CLAIM-05 mapped to test records, uncertainty intervals, and defensible wording. |
| [`REPRODUCIBILITY_STATUS.md`](REPRODUCIBILITY_STATUS.md) | Audit of reproduction prerequisites, one-command runner, and numerical consistency. |
| [`LITERATURE_AND_NOVELTY_INVENTORY.csv`](LITERATURE_AND_NOVELTY_INVENTORY.csv) | Deep comparison with 8 key published works (Trajectory Guard, DriftNet, AgentSentry, etc.). |
| [`KNOWN_LIMITATIONS_AND_OPEN_QUESTIONS.md`](KNOWN_LIMITATIONS_AND_OPEN_QUESTIONS.md) | Honest critique of finite sample size ($N=20$), small calibration set ($n=5$), and open questions. |
| [`AUDIT_METHODS_AND_EXCLUSIONS.md`](AUDIT_METHODS_AND_EXCLUSIONS.md) | Methodology used to audit the implementation, run test suites, and extract findings. |
| [`FILE_MANIFEST.csv`](FILE_MANIFEST.csv) | Machine-readable manifest of all files, sizes, and SHA-256 cryptographic checksums. |
| `source/` | Full, unredacted source tree (`src/`, `configs/`, `data/`, `tests/`, `paper/`, `scripts/`, `reports/`). |

---

## 4. Key Verified Empirical Takeaways

1. **Gate G3 & G4 Empirical Finding**:
   - Simpler transition bigram ($B1$) and unconditioned sequence ($B4$) baselines trigger **$100.00\%$ false interruptions on benign tasks** ($FIR = 2/2$) in live closed-loop deployment, completely destroying agent utility.
   - Observation content detectors ($B3$) falsely interrupt **$50.00\%$** of legitimate tasks when observations quote untrusted strings.
   - **AgentWatch-A (GoalConditionedGRU Full Monitor)** is the only system achieving **$100.00\%$ ASR reduction with $0.00\%$ false interruption of benign tasks**, preserving full agent utility.
2. **Operational Latency**:
   - Average per-decision CPU inference latency is **$1.61\text{ ms}$** (p95 = $1.91\text{ ms}$, max = $1.94\text{ ms}$), far outperforming the $50\text{ ms}$ operational budget with **\$0.00 cloud token cost**.
3. **Critical Statistical Limitation**:
   - Total canonical traces: $N=20$ ($n=5$ calibration, $N=15$ held-out test).
   - In Track 2 live intervention ($N=2$ benign tasks), the Fisher exact test on false interruption achieves $p = 0.1667$ despite an absolute separation of $100\%$ ($ARR = 1.00$), because with $N=2$ per group, $p < 0.05$ is mathematically impossible. A larger sample ($N \ge 30$) is recommended for high statistical power.
