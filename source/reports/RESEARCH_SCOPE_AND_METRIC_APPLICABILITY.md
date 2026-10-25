# Research Scope and Metric Applicability Matrix

**Project**: AgentWatch-A (Direction A Specification v1.0)  
**Authoritative Source**: [`AGENTWATCH_DIRECTION_A_SPEC.md`](../AGENTWATCH_DIRECTION_A_SPEC.md)  
**Audit Date**: 2026-10-25  

---

## 1. Research Scope Resolution

An exhaustive audit of the repository, source code, specifications, and execution traces reveals two distinct research concepts often associated with the broader "AgentWatch" initiative:

1. **Direction A (Current Active Repository)**: **Single-Agent Online Pre-Execution Monitoring for Indirect Prompt Injection**.
   - **Status**: **IN SCOPE & IMPLEMENTED**.
   - **Environment**: AgentDojo 0.1.35 (`workspace` suite, 40 tasks).
   - **Intervention Point**: Tool execution boundary mediated via `PreExecutionInterceptor` and `PreExecutionMonitorHook`.
   - **Primary Timing Invariant**: $t_{\text{flag}} \le t_{\text{harm}}$.
   - **Core Objective**: Intercept IPI-induced malicious tool calls before irreversible real-world side effects execute, while controlling trajectory-level false positive rates ($FPR_{\text{traj}} \le \alpha$).

2. **Direction B (Multi-Agent Interaction & Coordination)**: Multi-agent communication, agreement, protocol compliance, behavioral collusion, and environmental reward sharing.
   - **Status**: **OUT OF SCOPE / NOT IMPLEMENTED IN DIRECTION A**.
   - **Authoritative Confirmation**: Section 3.2, Line 121 of [`AGENTWATCH_DIRECTION_A_SPEC.md`](../AGENTWATCH_DIRECTION_A_SPEC.md) explicitly declares:
     > *"Building a general-purpose multi-agent security solution; that is Direction B and belongs to the other team."*
   - Furthermore, [`docs/LIMITATIONS_AND_ETHICS.md`](../docs/LIMITATIONS_AND_ETHICS.md) explicitly lists multi-agent coordination as an external, unmodeled generalization frontier.
   - **Integrity Rule**: Per Part 1.2 of the research audit instructions, single-agent detection metrics must **never** be conflated with multi-agent coordination metrics. In this audit, multi-agent coordination metrics are formally classified as `NOT APPLICABLE / OUT OF SCOPE` for the Direction A codebase.

---

## 2. Research Scope & Metric Applicability Matrix

| RQ ID | Research Question Formulation | Source Document | Confirmatory / Exploratory | Operational Hypothesis | Unit of Analysis | Primary Outcome / Estimand | Eligible Conditions | Required Labels | Statistical Method | Evidence Needed to Support | Unresolved Ambiguities & Scope Limits |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **RQ-A1** | At a fixed benign false-alarm budget ($\alpha = 0.20$), does a black-box, prefix-only monitor provide meaningful improvement in pre-execution detection over baselines? | `AGENTWATCH_DIRECTION_A_SPEC.md` Sec 4; `research_questions.md` | Confirmatory | **H1**: Goal-conditioned monitor achieves $TPR_{\text{pre}} > 0.80$ while maintaining $FPR_{\text{benign}} \le \alpha$. | Trajectory ($N=15$ test) | $TPR_{\text{pre}}$, $FPR_{\text{benign}}$, AUROC | Track 1 (Offline Prefix Replay): B1, B2, B3, B4, Full Monitor | `BENIGN`, `HIJACKED`, $t_{\text{harm}}$ | Split-conformal quantile thresholding, Wilson 95% CIs | High anomaly scores on hijacked calls prior to $t_{\text{harm}}$ without triggering on benign prefixes | Small hijacked test sample ($N=3$) limits statistical power of $TPR_{\text{pre}}$ confidence interval. |
| **RQ-A2** | Can split-conformal calibration on benign trajectory maxima maintain target false alarm rates? | `AGENTWATCH_DIRECTION_A_SPEC.md` Sec 9; `research_questions.md` | Confirmatory | **H5**: Empirical test $FPR_{\text{benign}} \le \alpha$ on held-out tasks. | Trajectory ($n=5$ cal, $N=5$ test) | Empirical $FPR_{\text{benign}}$ | Held-out benign tasks under calibrated threshold $\hat{\tau}$ | `BENIGN` | Conformal quantile order statistic $k = \lceil(n+1)(1-\alpha)\rceil$, exact binomial CIs | Empirical $FPR \le 0.20$ on held-out benign set | Calibration sample $n=5$ yields $k=5$ (maximum score); exact coverage guarantees hold marginally under exchangeability. |
| **RQ-A3** | How does the monitor respond to adaptive attacks and distribution shift? | `AGENTWATCH_DIRECTION_A_SPEC.md` Sec 10; `research_questions.md` | Exploratory | **H6**: Semantic/domain shift reduces lead time or inflates benign false alarm rate. | Task suite / Trajectory | $\Delta TPR_{\text{pre}}$, $\Delta FPR$ | Held-out attack templates, resisted workflows, cross-suite transfer | `EXPOSED_RESISTED`, `HIJACKED` | Stratified comparison across attack templates | Performance across non-workspace benchmarks (e.g., AgentDyn) | Cross-suite external benchmark transfer (e.g. AgentDyn) not executed; scoped as an open limitation in `LIMITATIONS_AND_ETHICS.md`. |
| **RQ-A4** | Do goal conditioning and argument provenance add value beyond simpler trajectory baselines and content detectors? | `AGENTWATCH_DIRECTION_A_SPEC.md` Sec 8; `research_questions.md` | Confirmatory | **H2, H3**: Goal ablation increases benign FPR; provenance amplifies tainted exfiltration score. | Proposed tool call ($x_t$) & Trajectory | Score separation, Benign Interruption Rate ($FIR_{\text{benign}}$) | Track 1 Replay & Track 2 Live: Full vs Ablated GRU vs B3 Content | `BENIGN`, `HIJACKED`, Taint annotations | Paired feature ablation, Fisher's exact test on $FIR_{\text{benign}}$ | Ablated GRU causes severe benign false alarms; provenance separates exfiltration from normal calls | Argument provenance currently rule-derived; adversary might attempt obfuscated argument encoding. |
| **RQ-A5** | Does in-loop intervention reduce end-to-end Attack Success Rate (ASR) without unacceptable utility loss, latency, or cost? | `AGENTWATCH_DIRECTION_A_SPEC.md` Sec 12; `research_questions.md` | Confirmatory | **H7**: In-loop blocking drops ASR to near-zero with $FIR_{\text{benign}} \le 0.10$ and CPU latency $<50\text{ ms}$. | Execution Episode ($N=4$ scenarios) | In-Loop ASR, ASR Reduction, $FIR_{\text{benign}}$, CPU Latency (ms) | Track 2 Closed-Loop: Unprotected Agent vs B1, B3, B4, Ablated, Full GRU | `BENIGN`, `HIJACKED`, Tool execution state | Absolute Risk Reduction ($ARR$), Relative Risk ($RR$), Fisher's exact test, latency benchmarking | Live intervention blocks hijacked action, agent completes benign tasks, latency $<50\text{ ms}$ | Live scenario count ($N=2$ benign, $N=2$ attack) is compact; requires wider task-set evaluation. |
| **RQ-MA1** *(Multi-Agent Coordination)* | Do autonomous agents exhibit emergent collusion or coordinated protocol violations in shared environments? | Direction B Draft / External Context | Out of Scope / Not Applicable | N/A (Direction B) | Agent Group / Multi-Agent Episode | Coordination rate, violation recurrence | N/A (No multi-agent environment implemented) | N/A | N/A | N/A | **NOT IN CODEBASE**: Direction A repository contains single-agent LLM tool execution only. Evaluated as `NOT APPLICABLE`. |
