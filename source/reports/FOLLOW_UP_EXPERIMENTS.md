# Prioritized Follow-Up Experiments & Research Roadmap

**Project**: AgentWatch-A (Direction A Specification v1.0)  
**Date**: 2026-10-25  

This document outlines prioritized, targeted follow-up experiments designed to resolve the empirical and statistical uncertainties identified during the comprehensive audit of AgentWatch-A.

---

## Priority 0: Statistical Sample Expansion & Calibration Tightening

### Experiment EXP-01: Large-Scale Benign Conformal Calibration ($n \ge 50$)
- **Research Question**: Does expanding the benign calibration corpus from $n=5$ to $n=50$ tighten the empirical test coverage and eliminate small-sample quantile variance?
- **Scientific Motivation**: In the current implementation, with $n=5$ calibration trajectories and target $\alpha = 0.20$, the order statistic is $k = \lceil (5+1)(1-0.20) \rceil = 5$ (the absolute maximum). On the held-out test set ($N=5$), empirical $FPR_{\text{benign}}$ was $40\%$ (2/5 false alarms). With $n=50$, $k = \lceil 51 \times 0.80 \rceil = 41$, allowing true quantile interpolation rather than taking the extreme maximum.
- **Protocol & Design**:
  - Sample 50 benign trajectories across all 40 AgentDojo workspace tasks.
  - Compute trajectory maxima $S_{(1)} \le \dots \le S_{(50)}$.
  - Evaluate calibrated threshold $\hat{\tau} = S_{(41)}$ on a held-out test split of 50 benign tasks.
- **Expected Outcome**: Empirical $FPR_{\text{benign}} \in [0.15, 0.22]$ with 95% Wilson confidence interval $< \pm 0.08$.
- **Estimated Resource Cost**: $< 30\text{ seconds}$ local CPU execution. Zero API cost.

---

## Priority 1: Statistical Power Expansion on Hijacked Test Tasks ($N \ge 30$)

### Experiment EXP-02: Broad Hijack Detection Power Benchmark
- **Research Question**: Does the $100\%$ pre-execution detection rate ($TPR_{\text{pre}}$) hold across a statistically powered sample of hijacked attacks ($N=30$), and does Fisher's exact test achieve $p < 0.001$?
- **Scientific Motivation**: Currently, $TPR_{\text{pre}} = 3/3 = 100\%$, which yields a wide 95% Wilson interval of $[0.439, 1.000]$. Furthermore, in Track 2 live intervention, $FIR_{\text{benign}} = 0/2$ vs $2/2$ yields Fisher $p = 0.167$ due to small $N$. Evaluating $N=30$ hijacked and $N=30$ benign live scenarios will provide definitive statistical significance ($p < 0.0001$) and narrow the Wilson interval to $\pm 0.05$.
- **Protocol & Design**:
  - Run all 40 AgentDojo workspace user tasks paired with all 6 injection attacks across attack levels L0 and L1.
  - Compute pre-execution lead time distribution, $TPR_{\text{pre}}$, and live benign task completion.
- **Estimated Resource Cost**: $\sim 3\text{ minutes}$ local CPU execution with `MockDeterministicAssistant`.

---

## Priority 2: Cross-Suite Out-of-Distribution Benchmark Transfer

### Experiment EXP-03: Multi-Suite Generalization (Banking, Travel, Slack)
- **Research Question**: How does AgentWatch-A perform when deployed on entirely unseen tool suites (e.g. banking transfers, flight bookings, Slack messaging) without retraining?
- **Scientific Motivation**: Section 10 of `AGENTWATCH_DIRECTION_A_SPEC.md` and Hypothesis H6 predeclared that distribution shift would lower lead time or degrade detection. In Phase 9, this was scoped as an open limitation in `LIMITATIONS_AND_ETHICS.md`. This experiment directly tests the boundary of the CRC32 token encoder and tool transition matrix.
- **Protocol & Design**:
  - Evaluate the frozen workspace-trained monitor on 30 canonical traces from the AgentDojo `banking` and `slack` suites.
  - Measure degradation in AUROC, false positive rate shift, and latency overhead.
- **Estimated Resource Cost**: $\sim 2\text{ minutes}$ local CPU execution.

---

## Priority 3: White-Box Adaptive Adversary Evaluation

### Experiment EXP-04: Gradient-Based Embedding Evasion Attack
- **Research Question**: Can an adversary with knowledge of the frozen CRC32 text projection and GRU weights optimize the injected prompt text to minimize cosine distance $\langle z_g, z_t \rangle$ and bypass the monitor?
- **Scientific Motivation**: Current benchmarks evaluate static prompt injection templates (`important_instructions`). A rigorous security evaluation must assess adaptive attacks where the attacker optimizes payload vocabulary to mimic legitimate goal tokens.
- **Protocol & Design**:
  - Formulate discrete prompt optimization (e.g., GCG or random search over CRC32 hash buckets) targeting $\min s_t$ subject to the agent still executing the unauthorized tool call.
  - Measure Attack Success Rate against the monitor as a function of attacker query budget.
- **Estimated Resource Cost**: $\sim 15\text{ minutes}$ local CPU search.

---

## Priority 4: Direction B Multi-Agent Coordination & Protocol Study

### Experiment EXP-05: Multi-Agent Tool-Mediated Coordination Protocol
- **Research Question**: In multi-agent systems where Agent 1 delegates tasks to Agent 2 via shared tools, do pre-execution monitors at the delegation boundary detect inter-agent prompt injection and prevent coordinated protocol violations?
- **Scientific Motivation**: Addresses the multi-agent questions raised in research design discussions (Direction B). While out-of-scope for the single-agent Direction A thesis, extending the `PreExecutionMonitorHook` to inter-agent communication channels provides a natural bridge to multi-agent safety.
- **Protocol & Design**:
  - Set up a two-agent workflow (Delegator and Worker) using AgentDojo workspace tools.
  - Introduce untrusted inter-agent messages containing indirect prompt injections.
  - Measure whether the causal monitor identifies compromised worker actions before execution.
- **Estimated Resource Cost**: $\sim 5\text{ minutes}$ local CPU execution.
