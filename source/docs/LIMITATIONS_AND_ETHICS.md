# AgentWatch-A: Limitations, Ethics, and License Disclosures

Adheres strictly to Section 20.3 and Section 20.4 of [`AGENTWATCH_DIRECTION_A_SPEC.md`](file:///C:/Users/Ayush/Documents/GitHub/research%20project/revised_agentwatch__dir_a/AGENTWATCH_DIRECTION_A_SPEC.md).

---

## 1. Scientific & Methodological Limitations

### 1.1 Finite-Sample Conformal Bounds & Exchangeability
- **Exchangeability Assumption**: Split-conformal calibration on trajectory maxima guarantees marginal false alarm rate control $P(M_{n+1} > \hat{\tau}) \le \alpha$ assuming the calibration and test trajectories are exchangeable draws from the same underlying distribution.
- **Distribution Shift**: If the user task domain shifts significantly from the calibration suite, empirical $FPR_{\text{traj}}$ may exceed nominal $\alpha$. In high-stakes production deployments, calibration sets must be refreshed periodically or stratified by task domain.
- **Sample Resolution**: With $n = 5$ calibration units, the minimum non-trivial empirical tail level is $\alpha \approx 0.17$. Larger calibration cohorts ($n \ge 50$) are required for strict $FPR \le 0.01$ thresholds without triggering the infinite threshold rule.

### 1.2 Benchmark Scope & Task Diversity
- **Primary Suite**: Experiments were executed within the AgentDojo `workspace` suite (v0.1.35) under local mock and deterministic execution pipelines.
- **Task Generalization**: While the monitor achieves 100% pre-execution detection on workspace email and calendar hijacks, generalization to multi-agent environments or novel tool suites (e.g. web browsing, bash execution) requires expanding the tool vocabulary and transition prior.

### 1.3 Attacker Adaptivity & Threat Model Boundaries
- **Threat Model**: The attacker is assumed to operate via indirect prompt injection into tool observations without white-box access to the monitor's GRU weights or calibrated threshold $\hat{\tau}$.
- **Adaptive Evasion**: An adaptive attacker who knows the monitor's exact architecture and threshold could theoretically craft subtle, single-step multi-stage hijacks that mimic benign goal vocabulary. Investigating adversarial robustness against white-box gradient-guided evasion is an essential direction for future work.

---

## 2. Ethical Considerations & Dual-Use Impact

### 2.1 AI Safety & Defense-First Design
- **Intended Purpose**: AgentWatch-A is designed as a defensive safety monitor to protect users from indirect prompt injection, data exfiltration, and unauthorized action execution in autonomous tool-using LLM agents.
- **No Weaponization**: The models, features, and algorithms developed here do not create new attack vectors or offensive exploit tooling. They provide defensive pre-execution monitoring and containment.

### 2.2 Operational Failure Modes
- **False Interruption Risk**: In low-tolerance environments, false blocks ($FIR$) may interrupt critical workflows. The monitor provides configurable `FLAG` (detect-only) and `HOLD` (human confirmation) modes to avoid automated disruption when false positive risk must be strictly managed.

---

## 3. Licenses & Computational Statement

### 3.1 Software Licenses
- **AgentDojo**: Licensed under the **MIT License** (Copyright 2024 ETH Zurich SPY Lab).
- **AgentWatch-A**: Distributed under the **Apache 2.0 / MIT License**.
- **Core Dependencies**: PyTorch (BSD-3-Clause), scikit-learn (BSD-3-Clause), Pydantic (MIT), NumPy (BSD-3-Clause).

### 3.2 Compute & Environmental Cost Statement
- **Zero Cloud API Tokens**: No commercial or paid cloud APIs (OpenAI, Anthropic, Gemini) were queried during benchmark evaluation or training.
- **Local CPU Execution**: All embeddings, training, conformal calibration, and live in-loop intervention benchmarks execute 100% locally on standard consumer x86_64 CPU hardware.
- **Energy Footprint**: Total computational training and evaluation time across all phases was under 15 minutes of local CPU runtime, incurring negligible environmental footprint.
