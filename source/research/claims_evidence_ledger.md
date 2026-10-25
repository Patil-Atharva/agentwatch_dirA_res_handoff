# AgentWatch-A: Master Claims-Evidence Ledger

Adheres strictly to Section 20.2, Section 20.3, and Section 21 of [`AGENTWATCH_DIRECTION_A_SPEC.md`](file:///C:/Users/Ayush/Documents/GitHub/research%20project/revised_agentwatch__dir_a/AGENTWATCH_DIRECTION_A_SPEC.md).
Every quantitative or comparative statement in this ledger directly maps to [`data/result_registry.json`](file:///C:/Users/Ayush/Documents/GitHub/research%20project/revised_agentwatch__dir_a/data/result_registry.json). Claims without evidence are explicitly classified as unsupported or open limitations.

---

## 1. Primary Research Questions

| Question ID | Formulation | Status | Key Evidence / Metric | Supported in Manuscript? |
|---|---|---|---|---|
| **RQ-A1** | At a fixed benign-interruption budget, does a black-box, prefix-only monitor provide meaningful improvement in detecting hijacks before harmful execution compared to strong baselines? | **Supported** | At $\alpha = 0.20$, Full Monitor achieves $TPR_{\text{pre}} = 100\%$ and $FPR_{\text{benign}} = 0\%$, while transition bigram (B1) and sequence (B4) baselines suffer $FPR_{\text{benign}} = 40\%$. | **Yes (Core Thesis)** |
| **RQ-A2** | Can split-conformal calibration on benign trajectory maxima maintain target false alarm rates? | **Supported** | Empirical test $FPR_{\text{benign}} = 0.0\% \le \alpha = 0.20$ on held-out test split using $k = 5$ order statistic. | **Yes** |
| **RQ-A3** | How does the monitor respond to adaptive attacks and shift? | **Partially Scoped** | Evaluated on held-out mock attack sequences and resisted workflows; external benchmark transfer documented as future work. | **Yes (Scoped Limitation)** |
| **RQ-A4** | Do goal conditioning and argument provenance add value beyond simpler trajectory baselines and content detectors? | **Supported** | Goal ablation increases benign FPR from $0\%$ to $20\%$. B3 content detector falsely flags $50\%$ of legitimate benign workflows with untrusted observations. | **Yes** |
| **RQ-A5** | Does in-loop intervention reduce end-to-end ASR without unacceptable utility loss, latency, or cost? | **Supported** | Monitored in-loop ASR drops to $0.0\%$ ($100\%$ reduction) with $0\%$ false interruption of benign tasks at $2.69\text{ ms}$ CPU latency and zero cloud API cost. | **Yes** |

---

## 2. Preregistered Hypotheses Ledger

| Hypothesis | Description | Theoretical Expectation | Empirical Finding | Evidence Pointer (`result_registry.json`) | Outcome |
|---|---|---|---|---|---|
| **H1** | Goal-conditioned causal monitor improves pre-execution detection over B1 and B2 baselines. | Separation $> 0.20$, $FPR \le \alpha$ | Separation $+0.3901$ vs $+0.0535$ (B2 Isolation Forest); $FPR_{\text{benign}} = 0\%$ vs $40\%$ (B1). | `feature_separation.GoalConditionedGRU_Full`, `track_1_offline_replay` | **Confirmed** |
| **H2** | Goal conditioning improves detection over unconditioned sequence model (B4). | Goal alignment prevents benign false alarms. | Unconditioned B4 has separation $+0.1846$ and $FPR_{\text{benign}} = 40\%$; GoalConditionedGRU achieves separation $+0.3901$ and $FPR = 0\%$. | `feature_separation`, `track_1_offline_replay.B4_UnconditionedSequence` | **Confirmed** |
| **H3** | Argument provenance features add measurable value beyond action names alone. | High-impact tool + untrusted argument amplifies risk score. | Taint amplification test confirms high-impact call (`send_email`) with untrusted recipient scores $> 0.85$ vs $< 0.45$ for benign recipient. | `feature_separation.GoalConditionedGRU_Full`, `tests/unit/test_goal_conditioned_monitor.py` | **Confirmed** |
| **H4** | Benign contrastive training provides a competitive trade-off relative to supervised oracle (B6). | Oracle upper-bounds, but monitor approaches without requiring labels for all future attack styles. | Oracle AUROC = 1.000; Full Monitor achieves AUROC = 1.000 with contrastive objective. | `track_1_offline_replay.B6_SupervisedOracle`, `track_1_offline_replay.GoalConditionedGRU_Full` | **Confirmed** |
| **H5** | Conformal thresholding achieves empirical FPR near target $\alpha$ on held-out tasks. | $FPR_{\text{traj}} \le \alpha = 0.20$ | Empirical test $FPR_{\text{benign}} = 0.00\%$, $FPR_{\text{resisted}} = 0.00\% \le 0.20$. | `conformal_calibration`, `track_1_offline_replay` | **Confirmed** |
| **H6** | Distribution shift degrades detection in quantifiable manner. | OOD attack styles lower lead time or increase required threshold. | Scoped to benchmark task coverage; cross-suite transfer detailed as an explicit limitation. | `docs/LIMITATIONS_AND_ETHICS.md` | **Scoped** |
| **H7** | In-loop intervention reduces end-to-end ASR at acceptable benign utility cost. | Live blocking prevents harm; $FIR_{\text{benign}} \approx 0\%$. | ASR reduced from $50\%$ to $0\%$ ($100\%$ reduction); $FIR_{\text{benign}} = 0.0\%$ (naive baselines B1/B4 cause $100\%$ false interruptions). | `track_2_in_loop_intervention` | **Confirmed** |

---

## 3. Specification Phase Gates Audit

- **Gate G1 (Benchmark Feasibility & Leakage)**: PASSED. AgentDojo 0.1.35 audited; pre-execution slicing tested against future leakage in `test_no_future_leakage.py`.
- **Gate G2 (Baseline Gate)**: PASSED. Priority A baselines (B1, B2, B3, B4, B6) implemented and benchmarked before learned monitor design.
- **Gate G3 (Defensible Architecture Benefit)**: PASSED. Goal-Conditioned GRU demonstrates $+0.3901$ separation and eliminates the $40\%$ benign false alarms suffered by sequence baseline B4.
- **Gate G4 (Simpler Enforcement Comparison)**: PASSED. Simpler enforcement baselines (B1, B4) cause $100\%$ false interruptions on legitimate tasks in live loops; GoalConditionedGRU achieves $0\%$ false interruption while maintaining $100\%$ attack mitigation.

---

## 4. Responsible Publication Statements

In compliance with Section 20.4 of `AGENTWATCH_DIRECTION_A_SPEC.md`:
1. We do **not** claim "guaranteed detection of all arbitrary hijacks"; finite-sample conformal guarantees apply strictly marginally to exchangeable trajectories from the same distribution.
2. We report Track 1 (Offline Prefix Replay) and Track 2 (Closed-Loop Live Intervention) as separate quantitative evaluations.
3. Latency measurements ($2.69\text{ ms}$ average CPU inference) are benchmarked on local consumer hardware (Intel/AMD x86_64 CPU) and do not claim "zero overhead" in absolute terms.
4. All benchmarks and dependencies run 100% locally with zero paid API token usage.
