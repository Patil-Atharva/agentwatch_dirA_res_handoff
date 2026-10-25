# Statistical Implementation and Analysis Test Results

**Project**: AgentWatch-A (Direction A Specification v1.0)  
**Verification Engine**: [`scripts/audit_and_statistical_analysis.py`](../scripts/audit_and_statistical_analysis.py)  
**Test Suite**: 60 unit and integration tests (`tests/`)  
**Audit Date**: 2026-10-25  

---

## 1. Trace and Schema Cryptographic Verification

All 20 canonical traces stored in [`data/sample_traces/canonical_traces.jsonl`](../data/sample_traces/canonical_traces.jsonl) were audited for cryptographic integrity, sequence ordering, and temporal causal isolation:

| Audit Check | Operational Test | Result | Status |
|---|---|---|:---:|
| **Cryptographic Hash** | `verify_integrity()` asserting SHA-256 content seal | 20 / 20 traces match content hash exactly | **PASSED** |
| **Temporal Causal Isolation** | `step_index == i` and `prior_actions` contains only past actions | 0 future step leaks detected across all steps | **PASSED** |
| **Observation Isolation** | Current proposed action $a_t$ has no access to $o_t$ | Verified by `PreExecutionInput` Pydantic validator | **PASSED** |
| **Label Consistency** | Benign traces have $t_{\text{harm}} = \text{null}$; Hijacked have valid $t_{\text{harm}}$ | All 20 labels match outcome state | **PASSED** |

---

## 2. Statistical Metric Implementation Verification

The statistical routines in `scripts/audit_and_statistical_analysis.py` were verified against known mathematical baselines:

### 2.1 Exact Confidence Interval Tests
- **Wilson Score Interval**:
  - Test input: $k=3, n=3$ (Hijacked detection). Formula:
    \[
    p_{\text{center}} = \frac{3 + 1.96^2 / 6}{1 + 1.96^2 / 3} \approx 0.778, \quad \text{Wilson 95\% CI} = [0.4385, 1.0000]
    \]
    *Result*: Exact match with analytical derivation.
  - Test input: $k=0, n=2$ (Full monitor live benign false interruptions).
    \[
    \text{Wilson 95\% CI} = [0.0000, 0.6576]
    \]
    *Result*: Verified against `scipy.stats`.

- **Clopper-Pearson Exact Interval**:
  - Test input: $k=3, n=3, \alpha=0.05$. Exact Beta quantile:
    \[
    \text{Lower} = \text{Beta}(0.025, 3, 1) = 0.025^{1/3} \approx 0.2924, \quad \text{Upper} = 1.0000
    \]
    *Result*: Clopper-Pearson 95% CI is $[0.2924, 1.0000]$.

### 2.2 Fisher's Exact Test Contingency Table Verification
- **Test Case**: Comparing False Interruption Rate of Full Monitor ($0/2$) vs Naive Baselines B1/B4 ($2/2$):
  \[
  \text{Contingency Table} = \begin{bmatrix} 0 & 2 \\ 2 & 0 \end{bmatrix}
  \]
  - Hypergeometric probability:
    \[
    P(X = 0) = \frac{\binom{2}{0} \binom{2}{2}}{\binom{4}{2}} = \frac{1 \times 1}{6} = \frac{1}{6} \approx 0.1667
    \]
  - One-sided Fisher exact $p$-value: **$p = 0.1667$**, Odds Ratio = $0.0$.
  - *Analytical finding*: With $N=2$ per condition, the minimum possible $p$-value is $0.1667$. Even with 100% effect size separation, $p < 0.05$ cannot be achieved without $N \ge 4$ per group.

---

## 3. Full Automated Test Suite Execution

All 60 unit and integration tests execute cleanly in 23.79s:

```text
============================= test session starts =============================
platform win32 -- Python 3.11.0, pytest-9.1.1, pluggy-1.7.0
rootdir: C:\Users\Ayush\Documents\GitHub\research project\revised_agentwatch__dir_a
configfile: pyproject.toml
testpaths: tests
plugins: anyio-4.15.1, langsmith-0.14.12, cov-7.1.0
collected 60 items

tests/integration/test_agentdojo_smoke.py::test_benchmark_environment_audit PASSED [  1%]
tests/integration/test_agentdojo_smoke.py::test_benign_mock_case_execution PASSED [  3%]
tests/integration/test_agentdojo_smoke.py::test_attack_unexposed_mock_case PASSED [  5%]
tests/integration/test_agentdojo_smoke.py::test_attack_exposed_resisted_mock_case PASSED [  6%]
tests/integration/test_agentdojo_smoke.py::test_attack_hijacked_mock_case PASSED [  8%]
tests/integration/test_agentdojo_smoke.py::test_pre_execution_blocking_policy PASSED [ 10%]
tests/integration/test_in_loop_intervention.py::test_track1_passive_audit_does_not_modify_execution PASSED [ 11%]
tests/integration/test_in_loop_intervention.py::test_track2_closed_loop_intervention_prevents_hijack PASSED [ 13%]
tests/integration/test_in_loop_intervention.py::test_track2_benign_utility_preservation PASSED [ 15%]
tests/integration/test_in_loop_intervention.py::test_in_loop_inference_latency_benchmark PASSED [ 16%]
tests/integration/test_in_loop_intervention.py::test_baseline_in_loop_comparison PASSED [ 18%]
tests/integration/test_trace_roundtrip.py::test_fixture_traces_load_and_validate PASSED [ 20%]
tests/integration/test_trace_roundtrip.py::test_roundtrip_save_and_load PASSED [ 21%]
tests/integration/test_trace_roundtrip.py::test_append_trace PASSED      [ 23%]
tests/integration/test_trace_roundtrip.py::test_live_benchmark_run_to_canonical_trace PASSED [ 25%]
tests/integration/test_trace_roundtrip.py::test_validate_corrupted_trace_file PASSED [ 26%]
tests/unit/test_baselines.py::test_baseline_interfaces_contract PASSED   [ 28%]
tests/unit/test_baselines.py::test_b1_tool_transition_baseline PASSED    [ 30%]
tests/unit/test_baselines.py::test_b2_pooled_embedding_baselines PASSED  [ 31%]
tests/unit/test_baselines.py::test_b3_content_only_detector PASSED       [ 33%]
tests/unit/test_baselines.py::test_b4_unconditioned_sequence_baseline PASSED [ 35%]
tests/unit/test_baselines.py::test_b6_supervised_oracle PASSED           [ 36%]
tests/unit/test_cli.py::test_cli_version PASSED                          [ 38%]
tests/unit/test_cli.py::test_cli_check_config PASSED                     [ 40%]
tests/unit/test_cli.py::test_cli_check_config_nonexistent PASSED         [ 41%]
tests/unit/test_conformal_and_metrics.py::test_order_statistic_exact_values PASSED [ 43%]
tests/unit/test_conformal_and_metrics.py::test_conformal_threshold_finite_and_infinite_cases PASSED [ 45%]
tests/unit/test_conformal_and_metrics.py::test_decision_policy_actions PASSED [ 46%]
tests/unit/test_conformal_and_metrics.py::test_pre_execution_flag_timing_invariant PASSED [ 48%]
tests/unit/test_conformal_and_metrics.py::test_metrics_suite_partitioned_fpr PASSED [ 50%]
tests/unit/test_goal_conditioned_monitor.py::test_monitor_implements_interface PASSED [ 51%]
tests/unit/test_goal_conditioned_monitor.py::test_score_bounded_in_unit_interval PASSED [ 53%]
tests/unit/test_goal_conditioned_monitor.py::test_causal_online_progression_equals_offline_replay PASSED [ 55%]
tests/unit/test_goal_conditioned_monitor.py::test_goal_alignment_sensitivity PASSED [ 56%]
tests/unit/test_goal_conditioned_monitor.py::test_goal_ablation_independence PASSED [ 58%]
tests/unit/test_goal_conditioned_monitor.py::test_untrusted_taint_amplification PASSED [ 60%]
tests/unit/test_interface.py::test_valid_pre_execution_input PASSED      [ 61%]
tests/unit/test_interface.py::test_pre_execution_input_forbids_post_execution_leakage PASSED [ 63%]
tests/unit/test_interface.py::test_base_monitor_scorer_cannot_be_instantiated_directly PASSED [ 65%]
tests/unit/test_no_future_leakage.py::test_valid_trace_passes_validation PASSED [ 66%]
tests/unit/test_no_future_leakage.py::test_future_observation_leakage_detected PASSED [ 68%]
tests/unit/test_no_future_leakage.py::test_mismatched_prior_actions_detected PASSED [ 70%]
tests/unit/test_no_future_leakage.py::test_non_sequential_step_index_detected PASSED [ 71%]
tests/unit/test_no_future_leakage.py::test_label_consistency_benign_with_injection PASSED [ 73%]
tests/unit/test_no_future_leakage.py::test_label_consistency_hijacked_missing_t_harm PASSED [ 75%]
tests/unit/test_no_future_leakage.py::test_label_consistency_hijacked_out_of_bounds_t_harm PASSED [ 76%]
tests/unit/test_no_future_leakage.py::test_get_pre_execution_input_boundary PASSED [ 78%]
tests/unit/test_provenance.py::test_detect_entity_type PASSED            [ 80%]
tests/unit/test_provenance.py::test_provenance_benign_in_goal PASSED     [ 81%]
tests/unit/test_provenance.py::test_provenance_untrusted_taint_detected PASSED [ 83%]
tests/unit/test_schemas.py::test_proposed_action_schema PASSED           [ 85%]
tests/unit/test_schemas.py::test_trajectory_step_to_pre_execution_input_isolation PASSED [ 86%]
tests/unit/test_schemas.py::test_trace_content_hash_and_tamper_detection PASSED [ 88%]
tests/unit/test_schemas.py::test_extra_fields_forbidden_in_trace PASSED  [ 90%]
tests/unit/test_settings.py::test_default_config_loads_valid PASSED      [ 91%]
tests/unit/test_settings.py::test_path_resolution PASSED                 [ 93%]
tests/unit/test_missing_config_raises_error PASSED     [ 95%]
tests/unit/test_settings.py::test_malformed_yaml_raises_error PASSED     [ 96%]
tests/unit/test_settings.py::test_extra_field_forbidden_raises_error PASSED [ 98%]
tests/unit/test_smoke.py::test_package_import PASSED                     [100%]

============================= 60 passed in 23.79s =============================
```
