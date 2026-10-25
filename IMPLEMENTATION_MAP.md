# AgentWatch-A: Implementation Map & Module Inventory

**Source Code Root**: `source/src/agentwatch_a/`  
**Test Suite**: `source/tests/` (60 passed in 23.79s)  

---

## 1. Codebase Directory and Module Map

| Module Path | Core Classes / Entry Points | Operational Role | Executed in Study? | Verified Tests |
|---|---|---|:---:|---|
| `src/agentwatch_a/cli.py` | `app`, `version()`, `doctor()`, `check_config()` | Typer-based command line interface | Yes | `tests/unit/test_cli.py` |
| `src/agentwatch_a/settings.py` | `Settings`, `MonitorConfig`, `CalibrationConfig` | Pydantic v2 configuration management | Yes | `tests/unit/test_settings.py` |
| `src/agentwatch_a/schemas.py` | `TrajectoryTrace`, `TrajectoryStep`, `ProposedAction` | Canonical Pydantic schemas with SHA-256 seals | Yes | `tests/unit/test_schemas.py` |
| `src/agentwatch_a/trace_store.py` | `load_traces_from_jsonl()`, `save_traces_to_jsonl()` | Trace I/O and tamper verification | Yes | `tests/integration/test_trace_roundtrip.py` |
| `src/agentwatch_a/provenance.py` | `extract_argument_provenance()`, `detect_entity_type()` | 7-dimensional argument provenance extraction | Yes | `tests/unit/test_provenance.py` |
| `src/agentwatch_a/benchmark/agentdojo_adapter.py` | `AgentDojoAdapter`, `PreExecutionInterceptor`, `MockDeterministicAssistant` | AgentDojo benchmark execution & pre-execution interception | Yes | `tests/integration/test_agentdojo_smoke.py` |
| `src/agentwatch_a/features/action_encoder.py` | `ToolActionEncoder`, `DeterministicTextEncoder` | Deterministic CRC32 feature projection | Yes | `tests/unit/test_goal_conditioned_monitor.py` |
| `src/agentwatch_a/models/interface.py` | `BaseMonitorScorer`, `PreExecutionInput` | Abstract monitor interface and causal boundary isolation | Yes | `tests/unit/test_interface.py` |
| `src/agentwatch_a/models/goal_conditioned_gru.py` | `GoalConditionedGRUMonitor` | Causal GRU recurrence, cosine projection, ablation toggle | Yes | `tests/unit/test_goal_conditioned_monitor.py` |
| `src/agentwatch_a/models/transition_baseline.py` | `ToolTransitionBaseline` (B1) | Markov tool transition baseline | Yes | `tests/unit/test_baselines.py` |
| `src/agentwatch_a/models/embedding_baseline.py` | `PooledEmbeddingAnomalyBaseline` (B2) | Isolation Forest and One-Class SVM anomaly baseline | Yes | `tests/unit/test_baselines.py` |
| `src/agentwatch_a/models/content_detector.py` | `ContentOnlyInjectionBaseline` (B3) | Observation regex and keyword scanner | Yes | `tests/unit/test_baselines.py` |
| `src/agentwatch_a/models/sequence_baseline.py` | `UnconditionedSequenceBaseline` (B4) | Unconditioned tool n-gram Markov baseline | Yes | `tests/unit/test_baselines.py` |
| `src/agentwatch_a/models/oracle_baseline.py` | `SupervisedOracleBaseline` (B6) | Supervised logistic regression upper bound | Yes | `tests/unit/test_baselines.py` |
| `src/agentwatch_a/calibration/conformal.py` | `ConformalCalibrator` | Split-conformal order statistic calculation | Yes | `tests/unit/test_conformal_and_metrics.py` |
| `src/agentwatch_a/policy/decision.py` | `DecisionPolicy` (`ALLOW`, `FLAG`, `HOLD`, `BLOCK`) | Multi-action runtime decision policy | Yes | `tests/unit/test_conformal_and_metrics.py` |
| `src/agentwatch_a/policy/hook.py` | `PreExecutionMonitorHook`, `PreExecutionHookTelemetry` | Live in-loop interception hook for agent loops | Yes | `tests/integration/test_in_loop_intervention.py` |
| `src/agentwatch_a/evaluation/metrics.py` | `compute_metrics_suite()`, `evaluate_trajectory_detection()` | Partitioned TPR/FPR, lead time, AUROC, AUPRC | Yes | `tests/unit/test_conformal_and_metrics.py` |

---

## 2. Production Scripts Inventory

| Script Path | Purpose | Execution Time | Output Artifacts |
|---|---|:---:|---|
| `scripts/reproduce_all.py` | Master 7-stage reproduction and zero-discrepancy audit pipeline | 3.89s | Console log; asserts `result_registry.json` |
| `scripts/audit_and_statistical_analysis.py` | Scientific statistical analysis, Wilson/CP CIs, Fisher exact tests | 1.20s | `reports/audit_statistical_summary.json` |
| `scripts/package_submission_artifact.py` | Anonymized double-blind conference package generator | 0.85s | `dist/agentwatch_a_anonymous_artifact.zip` |
| `scripts/train_monitor.py` | InfoNCE contrastive training runner for GoalConditionedGRU | 2.10s | `data/goal_conditioned_gru.pt` |
| `scripts/calibrate_and_evaluate.py` | Conformal calibration and Track 1 evaluation runner | 1.15s | `data/calibration_manifest.json` |
| `scripts/evaluate_in_loop.py` | Track 1 & Track 2 in-loop benchmark runner | 1.85s | `data/in_loop_evaluation_report.json` |
| `scripts/train_baselines.py` | Baseline model training runner | 0.95s | In-memory fitted baselines |
| `scripts/validate_traces.py` | Trace schema and SHA-256 integrity validator | 0.35s | Integrity report |
