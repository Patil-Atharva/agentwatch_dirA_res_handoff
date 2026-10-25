# AgentWatch-A: Research Questions and Preregistered Hypotheses

Adheres to Section 2.2 and Section 4 of AGENTWATCH_DIRECTION_A_SPEC.md.

## Primary Research Question
**RQ-A1:** At a fixed benign-interruption budget, does a black-box, prefix-only monitor provide a meaningful improvement in detecting successful indirect prompt-injection hijacks before a harmful tool call executes, compared with strong existing monitors and defenses?

## Supporting Research Questions
- **RQ-A2 (Calibration & Shift):** Can a threshold calibrated on held-out benign trajectories maintain its intended per-trajectory false-alarm rate on unseen tasks and agent models? Under which shifts does it fail?
- **RQ-A3 (Adaptive Robustness):** How much detection performance is lost when attack payloads are adapted to the target agent or monitor?
- **RQ-A4 (Feature Contribution):** Do goal conditioning and argument-provenance features help beyond simpler trajectory baselines and content-only classifiers?
- **RQ-A5 (Operational Value):** Does the monitor reduce end-to-end attack success without an unacceptable loss in legitimate task completion, latency, or cost?

## Hypotheses
- **H1:** Goal-conditioned causal monitor improves pre-execution detection at fixed trajectory FPR over simple transition and pooled-embedding baselines.
- **H2:** Goal conditioning improves detection over an unconditioned causal sequence model.
- **H3:** Argument-provenance features add measurable value beyond semantic and action-sequence features alone.
- **H4:** Benign-only training provides a useful trade-off relative to a supervised oracle.
- **H5:** Per-trajectory conformal thresholding achieves empirical FPR near target alpha under in-distribution held-out tasks.
- **H6:** Agent/task shift and adaptive attacks degrade detection, and degradation is quantifiable.
- **H7:** In-loop monitor intervention reduces end-to-end attack success at acceptable benign utility cost.
