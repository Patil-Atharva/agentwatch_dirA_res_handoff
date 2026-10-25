# AgentWatch Direction A — Research and Implementation Specification

**Document version:** 1.0  
**Prepared:** 23 October 2026  
**Status:** Research plan, not a claim of results or novelty  
**Primary user:** Researcher implementing Direction A with Google Antigravity  
**Working project name:** `AgentWatch-A` (temporary; check naming conflicts before public release)

> **Purpose of this document**  
> This is the authoritative project specification for Direction A. Use it to plan, implement, test, and evaluate the research project. Do not treat a proposed method, threshold, performance target, or candidate novelty claim as an established result. The project must be evidence-led: reproduce a minimal baseline and validate the benchmark protocol before building a complex learned monitor.

---

## Table of Contents

1. [Executive summary](#1-executive-summary)
2. [Research objective and scope](#2-research-objective-and-scope)
3. [Research context and novelty constraints](#3-research-context-and-novelty-constraints)
4. [Research questions and hypotheses](#4-research-questions-and-hypotheses)
5. [Threat model and assumptions](#5-threat-model-and-assumptions)
6. [System behavior and architecture](#6-system-behavior-and-architecture)
7. [Data, trace format, and label protocol](#7-data-trace-format-and-label-protocol)
8. [Model and feature specification](#8-model-and-feature-specification)
9. [Calibration and decision policy](#9-calibration-and-decision-policy)
10. [Benchmarks and experimental conditions](#10-benchmarks-and-experimental-conditions)
11. [Baselines and fair comparisons](#11-baselines-and-fair-comparisons)
12. [Metrics and statistical analysis](#12-metrics-and-statistical-analysis)
13. [Implementation plan and repository structure](#13-implementation-plan-and-repository-structure)
14. [Python environment and sandbox setup](#14-python-environment-and-sandbox-setup)
15. [Google Antigravity operating instructions](#15-google-antigravity-operating-instructions)
16. [Configuration, reproducibility, and experiment tracking](#16-configuration-reproducibility-and-experiment-tracking)
17. [Testing and quality requirements](#17-testing-and-quality-requirements)
18. [Implementation phases and go/no-go gates](#18-implementation-phases-and-gono-go-gates)
19. [Risk register and fallback plan](#19-risk-register-and-fallback-plan)
20. [Paper and artifact plan](#20-paper-and-artifact-plan)
21. [Definition of done](#21-definition-of-done)
22. [Suggested prompts for Antigravity](#22-suggested-prompts-for-antigravity)
23. [Reference links and citation checklist](#23-reference-links-and-citation-checklist)
24. [Appendix A — Canonical trace schema](#appendix-a--canonical-trace-schema)
25. [Appendix B — Experimental result table templates](#appendix-b--experimental-result-table-templates)
26. [Appendix C — Researcher's running checklist](#appendix-c--researchers-running-checklist)

---

## 1. Executive summary

### 1.1 The project in one paragraph

AgentWatch-A studies whether a **black-box, online, pre-execution monitor** can detect successful indirect prompt-injection (IPI) hijacks of a tool-using LLM agent before the proposed harmful tool call executes, while keeping interruptions of legitimate tasks acceptably low. The monitor may inspect the trusted user goal, the recorded history of prior tool calls and tool outputs, and the currently proposed tool call. It must not inspect future actions or the result of the action that is about to execute. The research compares simple and strong existing methods, tests outcome-based labels, evaluates per-trajectory false-alarm calibration, measures end-to-end effect when a monitor holds or blocks calls, and studies performance under task/model shift and adaptive attacks.

### 1.2 Core principle

**The goal is not to build the largest detector. The goal is to answer a well-defined research question with reproducible evidence.**

A new GRU, Transformer, graph layer, contrastive objective, provenance feature, or conformal threshold is not automatically novel. These components are established techniques or overlap with existing work. The contribution must be demonstrated through a specific capability, method, reliable dataset/evaluation artifact, or scientifically useful finding that the closest work has not already established.

### 1.3 Primary and fallback contributions

Candidate contributions—not promised findings—are:

1. An outcome-labeled collection of paired benign/attack traces, with injection exposure and environment-verified attack success separated.
2. A causal monitor evaluated strictly at the tool-execution boundary, using only the prefix and proposed call.
3. A per-trajectory thresholding protocol that targets a declared benign-interruption rate, with explicit checks of where exchangeability assumptions fail.
4. A head-to-head evaluation of benign-only monitoring, supervised trajectory detection, content-only detectors, and relevant defenses under held-out tasks, agent models, and adaptive attacks.
5. Negative results when simpler methods or existing enforcement-based defenses are as good as or better than the proposed monitor.

**Fallback paper:** if the learned model does not outperform strong baselines, pivot to a rigorous evaluation-and-analysis contribution only if the dataset, protocol, or findings are independently useful and carefully validated. Do not invent or overstate a contribution merely to keep the original architecture.

### 1.4 What success does not mean

Success does not mean hitting an arbitrary AUROC target, adding every planned feature, or obtaining a statistically significant difference on every metric. Success means answering the research questions honestly, using valid comparisons, reporting uncertainty and failure modes, and producing reproducible evidence.

---

## 2. Research objective and scope

### 2.1 Problem statement

An LLM agent receives a trusted user goal `g`, reads external or tool-returned content, and proposes tool calls while pursuing that goal. Some returned content may contain attacker-controlled instructions. An indirect prompt injection occurs when this untrusted content changes the agent's behavior in a way that serves the attacker rather than the authorized user goal.

At each decision point, AgentWatch-A observes the information available immediately before a proposed tool call is executed. It calculates a risk score and either allows the call, flags it for review, or holds/blocks it under a predeclared evaluation policy.

### 2.2 Primary research question

**RQ-A1:** At a fixed benign-interruption budget, does a black-box, prefix-only monitor provide a meaningful improvement in detecting successful IPI hijacks before a harmful tool call executes, compared with strong existing monitors and defenses?

Supporting questions:

- **RQ-A2 — Calibration and shift:** Can a threshold calibrated on held-out benign trajectories maintain its intended per-trajectory false-alarm rate on unseen tasks and agent models? Under which shifts does it fail?
- **RQ-A3 — Adaptive robustness:** How much detection performance is lost when attack payloads are adapted to the target agent or monitor?
- **RQ-A4 — Feature contribution:** Do goal conditioning and argument-provenance features help beyond simpler trajectory baselines and content-only classifiers?
- **RQ-A5 — Operational value:** Does the monitor reduce end-to-end attack success without an unacceptable loss in legitimate task completion, latency, or cost?

Do not add additional research questions unless they are necessary to answer the core question and the team has the evaluation budget to test them properly.

### 2.3 In scope

- Single-agent tool use.
- Indirect prompt injection originating in untrusted tool-returned content, such as simulated documents, messages, or webpages.
- Black-box access to the agent: no access to target-model hidden states or logits is required by the proposed monitor.
- Online/prefix-only score calculated before each proposed tool call executes.
- Trajectory-level false-alarm control, with finite-sample conformal thresholding as one candidate technique.
- Environment-verified outcome labels.
- Static attack templates, held-out attack templates, selected out-of-distribution tasks, and a feasible adaptive-attack study.
- Detection-only replay evaluation and separate closed-loop intervention evaluation.
- Latency, utility, uncertainty, robustness, ablations, reproducibility.

### 2.4 Out of scope for the first paper

Do not implement these unless a later research gate shows a precise need:

- Universal agent security or claims of zero-day detection.
- A claim that anomaly detection is equivalent to malicious-intent detection.
- Automated rollback of arbitrary external side effects.
- A generic MCP security proxy or a full product dashboard.
- Graph neural networks as the main architecture before a sequence baseline is established.
- Causal attribution from attention weights or unvalidated chain-of-thought/action similarity.
- Dependence on chain-of-thought text being present or faithful.
- A claim of 100% containment.
- Real external account operations or testing on systems without authorization.
- Building a general-purpose multi-agent security solution; that is Direction B and belongs to the other team.

### 2.5 Intended research outputs

- Version-controlled source code and configuration.
- A pinned benchmark/evaluation environment.
- Canonical JSONL traces plus a data dictionary; do not commit licensed or sensitive data if redistribution is not permitted.
- Reproducible baseline and model runs.
- A label-audit report.
- Metric tables, confidence intervals, plots, and a machine-readable results registry.
- An ablation and robustness report.
- A paper draft with conservative, evidence-backed claims.
- A README and clean-environment reproduction instructions.

---

## 3. Research context and novelty constraints

### 3.1 Closest known research to audit in full

The following references were identified in the literature review used to formulate this plan. Read each closest paper in full and inspect its public code or benchmark where available before finalizing novelty claims.

| Work | Why it matters to AgentWatch-A | Minimum action |
|---|---|---|
| [Trajectory Guard, arXiv:2601.00516](https://arxiv.org/abs/2601.00516) | Very close trajectory-based anomaly detection with task/trajectory alignment and sequence modeling. | Read full paper; verify methods, training objective, splits, metrics, code, and the exact difference from the proposed online constraint. Reproduce or make a documented, fair comparison. |
| [DriftNet, arXiv:2609.10892](https://arxiv.org/abs/2609.10892) | Supervised trajectory classification/localization and related synthetic data. | Understand how it labels per-step events and distinguish online pre-execution inference from retrospective/offline scoring. Confirm the repository/artifact status before claiming a reproducible baseline. |
| [AgentDrift, arXiv:2609.06972](https://arxiv.org/abs/2609.06972) | Synthetic labeled trajectory benchmark companion to DriftNet. | Audit for leakage, synthetic regularities, split policy, and whether its labels fit the threat model. Do not silently mix synthetic and environment-generated test traces. |
| [TraceAegis, arXiv:2510.11203](https://arxiv.org/abs/2510.11203) | Learns behavioral structure from normal traces. | Compare the benign-only premise, anomaly scoring, and sequence/behavior assumptions. |
| [AgentSentry, arXiv:2602.22724](https://arxiv.org/abs/2602.22724) | Inference-time IPI detection/mitigation with trajectory context. | Determine whether its code is runnable and what a fair reproduction would require. Do not omit it without a reason. |
| [AgentDojo, arXiv:2406.13352](https://arxiv.org/abs/2406.13352) | Main dynamic environment for evaluating prompt injection defenses. | Pin the exact code/task version, reproduce no-defense behavior, and audit security/utility checks. |
| [AgentDyn, arXiv:2602.03117](https://arxiv.org/abs/2602.03117) | Dynamic, open-ended out-of-distribution evaluation. | Treat as external evaluation; do not use it for training or threshold selection if reporting it as OOD. |
| [AutoDojo, arXiv:2606.15057](https://arxiv.org/abs/2606.15057) | Adaptive IPI evaluation that optimizes attacks against defenses. | Use it or a documented substitute if practical; report the exact attack budget and adaptation access. |
| [Agent-as-a-Proxy, arXiv:2602.05066](https://arxiv.org/abs/2602.05066) | Motivates adaptive attacks that manipulate an agent/monitor interaction. | Extract its attacker assumptions and add only a feasible, well-specified adaptive test. |
| [LlamaFirewall paper](https://arxiv.org/abs/2505.03574) and [official code](https://github.com/meta-llama/PurpleLlama/tree/main/LlamaFirewall) | Existing guardrail architecture with prompt-attack and alignment-oriented scanners. | Check installation, model/API requirements, license, and current interfaces. Compare when feasible. |
| [MELON](https://arxiv.org/abs/2502.05174) | A relevant inference-time prompt-injection defense based on behavior under a masked prompt. | Check the correct paper/version, reproduction prerequisites, and whether a fair comparison is feasible. |
| [Hidden-state probes, arXiv:2608.02657](https://arxiv.org/abs/2608.02657) | Alternative white-box signal for exposure/detection. | Treat as related work; it is not a direct black-box baseline if it requires hidden states unavailable to our monitor. |
| [Firewall-focused evaluation, arXiv:2510.05244](https://arxiv.org/abs/2510.05244) | Challenges the assumption that a learned monitor is always necessary and examines simple defenses and benchmark weaknesses. | Verify its exact title/authors/version and reproduce only what is needed for a fair comparison. |

The existence and relevance of these works **does not prove that every implementation is equivalent**. The full paper and code determine the overlap. Avoid conclusions based only on abstracts or secondary summaries.

### 3.2 What is not a novelty claim by itself

Do not claim novelty merely because the system:

- uses a GRU, Transformer, GAT, or sentence embedding model;
- combines contrastive learning with reconstruction loss;
- adds a goal embedding to trajectory detection;
- adds heuristic provenance flags for argument values;
- uses conformal prediction, calibration, or a threshold chosen on held-out benign data;
- logs traces and exposes a dashboard;
- evaluates another model on AgentDojo;
- measures attack success rate or F1;
- evaluates against paraphrased attacks without establishing a meaningful, previously unanswered result;
- combines several existing components in a pipeline.

### 3.3 Candidate novelty claim (must be verified)

The strongest initial positioning is an **evaluation-led claim**:

> We investigate whether a black-box, strictly pre-execution monitor can detect environment-verified successful agent hijacks at a controlled per-trajectory false-alarm rate, and quantify how its value changes under task/model shift and adaptive attack compared with strong existing monitors and enforcement-based defenses.

This is a candidate positioning statement—not a verified claim of novelty. Before the paper uses it, compare the exact threat model, inference-time information, intervention point, calibration unit, metrics, shifts, and baselines with the closest literature.

### 3.4 Distinguish four possible contributions

1. **Method contribution:** a demonstrably new decision rule or model capability, if one is found and justified.
2. **Evaluation contribution:** a rigorous online protocol, reliable environment-based labels, leakage-resistant splits, and fair baseline comparisons that resolve a meaningful uncertainty.
3. **Dataset/artifact contribution:** a reusable paired-run trace corpus with source/version/license metadata and outcome audits, if it can legally and practically be shared.
4. **Empirical finding:** an important, robust conclusion about monitor value, shift, calibration failure, feature contribution, or the superiority of a simpler defense.

A paper can emphasize an evaluation contribution or finding, but it must be materially useful—not merely a routine benchmark run.

### 3.5 Formal novelty audit process

For every proposed claim, create one row in `research/novelty_matrix.csv` with:

- `claim_id`
- exact proposed claim
- closest papers and versions
- exact overlap (method, setting, data, metrics)
- remaining difference
- cited evidence (section/page/repository path/issue)
- falsification test
- confidence in assessment (`low`, `medium`, `high`)
- decision (`keep`, `narrow`, `drop`, `needs_more_review`)
- review date

Search paper title, distinctive method terms, citations, cited-by results, source code, issues, and pull requests. Search alternate phrases. Record what was searched and what remains unverified. Never write “first-ever” unless the search protocol, scope, and evidence justify it—and a narrower claim is usually better.

---

## 4. Research questions and hypotheses

### 4.1 Hypotheses to preregister

| ID | Hypothesis | Comparison | Decision if unsupported |
|---|---|---|---|
| H1 | The goal-conditioned causal monitor improves pre-execution detection at a fixed trajectory-level FPR over simple tool-transition and pooled-embedding baselines. | Proposed monitor vs B1/B2. | Drop any claim that the learned model is superior; examine whether the evaluation result itself is useful. |
| H2 | Goal conditioning improves results beyond an otherwise matched unconditioned sequence model. | Matched with/without-goal ablation. | Remove goal conditioning from the proposed method if it does not help. |
| H3 | Argument-provenance features add value beyond semantic and action-sequence features. | Matched with/without-provenance ablation. | Remove provenance from the core system if it does not help; report the result. |
| H4 | Benign-only training provides a useful trade-off relative to a supervised oracle. | Benign-only vs supervised detector trained on labeled data. | Report the gap; do not claim parity unless a margin was declared in advance and the CI supports it. |
| H5 | Per-trajectory conformal thresholding produces an empirical FPR near its target under in-distribution held-out tasks. | Calibrated threshold vs target alpha and empirical held-out FPR. | Report failure and inspect dependence, finite calibration size, score shift, or implementation errors. |
| H6 | Agent/task shift and adaptive attacks reduce detection or coverage, and the magnitude can be quantified. | In-distribution vs cross-agent/OOD/adaptive. | Report null or counterintuitive results; do not presume degradation. |
| H7 | The monitor reduces end-to-end attack success at an acceptable utility cost. | No defense vs monitor intervention vs strong defense. | If a simpler defense dominates, reframe monitor as audit/triage only or pivot to evaluation. |

These hypotheses are deliberately falsifiable. Do not choose hypotheses after viewing the test results.

### 4.2 Primary endpoint

**Primary detection endpoint:** pre-execution true-positive rate (`TPR_pre`) on `HIJACKED` trajectories at a prespecified per-trajectory false-positive rate (`FPR_traj`), initially 5% as the main operating point. Report 1% only when the number of independent benign calibration units supports meaningful threshold resolution.

**Primary intervention endpoint:** end-to-end attack success rate (ASR) after the monitor holds/blocks calls, accompanied by benign task completion/utility and benign interruption rate.

AUROC/AUPRC are useful secondary threshold-free diagnostics; they must not replace the operating-point metrics.

### 4.3 Freeze the analysis plan

Before final testing, save a versioned `research/analysis_plan.md` that specifies:

- primary and secondary endpoints;
- definitions of positive and negative labels;
- train/validation/calibration/test splits;
- exclusions and their justification;
- calibration alpha values;
- model-selection and hyperparameter rules;
- random seeds and run counts;
- bootstrap unit and confidence interval method;
- ablations and shift tests;
- treatment of missing, failed, and interrupted runs;
- multiple-comparison caveats;
- decision gates and fallback rules.

Any later deviation must be logged in `research/decision_log.md` and explicitly disclosed in the paper.

---

## 5. Threat model and assumptions

### 5.1 System model

- A single tool-using agent has a trusted user goal `g`.
- The agent performs a sequence of reasoning/messages (optional), tool calls, and tool outputs.
- Some tool outputs are attacker-controlled or untrusted.
- A trusted interceptor sees the proposed action before the tool executor runs it.
- The monitor can be black-box relative to the agent model; it receives only the allowed trace prefix and proposed action.

### 5.2 Attacker capabilities

The attacker may:

- write malicious or misleading text into an untrusted source read by the agent;
- use the benchmark's allowed payload templates or documented paraphrase/obfuscation transformations;
- know the general class of monitor and adapt payloads under an explicitly defined black-box evaluation budget.

For the main threat model, the attacker cannot:

- change the trusted user goal or system prompt;
- modify model weights, monitor parameters, threshold, or logging code;
- tamper with the trusted tool interceptor;
- directly compromise the host process;
- execute arbitrary real-world side effects outside the simulated benchmark environment.

### 5.3 Trust assumptions

- The interceptor, score computation, and recorded telemetry are trusted components.
- Tool outputs have reliable trust labels from benchmark metadata or a documented policy.
- Ground-truth attack success is derived from the environment's security checker and audited—not inferred from a model's text alone.
- Benign training traces are not poisoned in the initial study.
- The monitor may itself be exposed to attacker-controlled text; adaptive attacks should test whether this weakens it.
- Chain-of-thought may be absent, hidden, or unfaithful. The main model must work without it.

### 5.4 Security and ethics restrictions

- Use local/simulated benchmark tools and fake accounts/data.
- Do not connect test runs to personal email, banking, GitHub, cloud, or production accounts.
- Do not include real API secrets in prompts, traces, notebooks, or Git history.
- Do not attack third-party services or create external side effects without explicit authorization.
- Keep any provider/API keys in an ignored `.env` file or environment variables.
- Review data licenses and terms before publishing traces or attack artifacts.

### 5.5 Required distinction

**Anomaly is not maliciousness.** A benign task can require an unusual action; an attack may be exposed but resisted; an injection may not be seen at all. Do not collapse these cases into one binary class in the dataset.

---

## 6. System behavior and architecture

### 6.1 The pre-execution boundary (non-negotiable)

At decision step `t`, the monitor can inspect:

- trusted user goal;
- prior steps `1 ... t-1`, including prior calls and their returned observations;
- trust/provenance metadata for those observations;
- the current proposed call `a_t` and its arguments;
- policy-defined tool metadata such as whether a tool is high impact.

It **must not** inspect:

- the result of executing `a_t`;
- future calls or future observations;
- the final task/attack label;
- `t_harm` as a feature;
- hidden test labels or any annotation generated after execution.

The monitor scores and makes a decision; only then can the harness execute, hold, or block the call. When storing a completed trace for analysis, it is acceptable to store the post-call observation, but the inference interface must make it impossible for the scoring function to access it at the decision point.

### 6.2 High-level data flow

```text
AgentDojo task and environment
        |
        v
Agent proposes a tool call
        |
        v
Pre-execution interceptor ----> trace event (prefix + proposed call only)
        |                                  |
        |                                  v
        |                         feature extraction
        |                                  |
        |                                  v
        |                         baseline/model scorer
        |                                  |
        |                                  v
        |                         calibrated threshold
        |                                  |
        +---- allow / flag / hold / block <-+
        |
        v
Tool executes only if policy allows
        |
        v
Observation + environment state/checker outcome logged after execution
        |
        v
Offline evaluation, label audit, statistics, reports
```

### 6.3 Required modules

1. **Benchmark adapter:** pins and invokes AgentDojo-compatible tasks/models/tools.
2. **Agent/tool interceptor:** creates the pre-execution decision event and enforces allow/hold/block.
3. **Trace collector:** writes immutable JSONL events/traces with run and version metadata.
4. **Outcome labeler:** derives BENIGN, UNEXPOSED, EXPOSED_RESISTED, HIJACKED from benchmark configuration, exposure records, and environment security checks.
5. **Schema validation:** rejects incomplete or invalid traces.
6. **Feature extractor:** embeds text and creates deterministic action/provenance features.
7. **Baseline suite:** simple transition and anomaly baselines, content detector adapter, sequence baseline, and selected existing defenses where feasible.
8. **Proposed model:** goal-conditioned causal sequence scorer; implement only after the baseline gate passes.
9. **Calibration module:** scores benign calibration runs and creates per-trajectory thresholds.
10. **Decision policy:** maps risk score + threshold to allow/flag/hold/block for evaluation.
11. **Evaluator:** computes detection, FPR, utility, ASR, lead time, latency, and shift metrics.
12. **Statistics/plots:** task-clustered uncertainty estimates, tables, and failure analysis.
13. **Experiment registry:** stores config hash, model/benchmark versions, seeds, split IDs, metrics, logs, and artifact locations.
14. **CLI:** reproducible commands for environment check, pilot, trace generation, training, calibration, evaluation, and report generation.

### 6.4 Keep the intervention policy simple

Start with two modes:

- `detect_only`: score and log, but do not change agent execution.
- `hold_or_block`: if the score crosses the frozen threshold, hold/block the proposed call. In the first version, prefer “hold for confirmation” when testing a practical intervention because blocking can alter subsequent agent behavior. The experimental policy must be explicitly stated.

Do not mix detection-only metrics with closed-loop mitigation results. A detector can catch a trace offline while being unable to prevent a harmful action in a live run if it flags too late.

---

## 7. Data, trace format, and label protocol

### 7.1 Main benchmark

Use **AgentDojo** as the main benchmark, subject to version/license/API verification. The upstream documentation warns that the API may evolve; therefore, record the exact package version, repository commit/tag, task-suite version, environment configuration, and dependency lock. The phrase “v1.2.2 tasks” in prior notes must not be assumed to be the Python package version. Confirm exactly which task revision and code commit are used.

Upstream references:

- Paper: https://arxiv.org/abs/2406.13352
- Official documentation: https://agentdojo.spylab.ai/
- Official repository: https://github.com/ethz-spylab/agentdojo
- PyPI package: https://pypi.org/project/agentdojo/

### 7.2 Optional external evaluation

- **AgentDyn:** external dynamic/OOD suite. Never use it for model training, threshold selection, or repeated tuning if it is reported as an untouched OOD evaluation. Document any benchmark adapter changes.
- **AutoDojo:** adaptive attacker/evaluation extension. Use only once core traces and labels are valid. Record attack budget, optimization queries, target defense access, and cost.
- **AgentDrift:** optional source of related comparisons or training experiments, not a substitute for environment-generated AgentDojo evaluation. Keep the synthetic benchmark results separate from environment-generated outcomes.

### 7.3 Outcome labels

Use the following mutually exclusive trajectory labels:

| Label | Definition | Primary metric treatment |
|---|---|---|
| `BENIGN` | No attack configured. | Core negative group. |
| `UNEXPOSED` | Attack was configured, but the injection content never surfaced in the agent's observations. | Report separately; also use as a benign hard-negative analysis group. |
| `EXPOSED_RESISTED` | Injection content surfaced, but the environment security checker says the attacker goal was not achieved. | Analyze separately. A flag may be useful early warning, but counting all such flags as true positives would overstate successful-hijack detection. |
| `HIJACKED` | The benchmark's environment-level security check confirms the attacker goal was achieved. | Primary positive class. |

Also record separate booleans/fields for `injection_configured`, `injection_visible`, `security_success`, `utility_success`, `agent_finished`, `harmful_action_proposed`, and `harmful_action_executed`.

The outcome label must not be guessed by a language model from the transcript. Use explicit benchmark outputs/security checkers, with manual audit to catch checker defects.

### 7.4 Step labels and `t_harm`

For each `HIJACKED` run, define `t_harm` as the **index of the first proposed tool call whose execution would satisfy the benchmark's attacker-goal condition**, immediately before execution. This is the relevant gate point for evaluating pre-execution detection. If the environment's checker does not identify a call boundary, document the proxy/limitation and do not pretend the boundary is exact.

For exposed-but-resisted runs, record the injection first-visible index and the highest-risk attempted call if available, but do not relabel the trajectory as HIJACKED.

### 7.5 Paired runs

Where the benchmark permits, use paired configurations for the same task/attack instance: no-defense agent, detector-only trace logging, and intervention enabled. Keep run IDs and configuration IDs linked. The agent may be nondeterministic; repeated runs and seeds are not interchangeable with independent user tasks. Report both the number of runs and the number of distinct tasks.

### 7.6 Trace fields (minimum)

Each trace must record:

- unique run and pair IDs;
- benchmark, suite, environment version/commit, task ID, injection ID, attack-template family;
- user goal and agent model/provider/version;
- random seed, model sampling parameters, timestamp, execution mode;
- injection configuration and exposure information;
- trajectory outcome and utility/security checker outputs;
- `t_harm` where known;
- for each step: prior prefix, proposed call, tool name, structured arguments, argument provenance, decision score, threshold, decision, and only after the call finishes, returned observation;
- runtime/latency, errors, retries, and exclusions;
- code commit and config hash.

Do not store chain-of-thought unless it is explicitly required and legally/ethically appropriate. The primary monitor must run with `thought = null`.

### 7.7 Label quality audit

Before model training and again before final results:

1. Randomly sample traces stratified by suite and label.
2. Compare labels with benchmark security/utility checker outputs and raw environment state.
3. Manually inspect at least 100 traces if the data volume allows; if fewer traces exist, inspect all and state the count.
4. Audit ambiguous cases, false positives/negatives in the checker, unexposed attacks, and runs that terminate unexpectedly.
5. Record disagreements, corrections, exclusion rules, and inter-annotator agreement if more than one reviewer is available.
6. Never silently change labels after viewing model errors. Preserve original and corrected labels with a documented reason.

### 7.8 Data splitting and leakage prevention

Required split principles:

- Split by **user task ID**, not randomly by step or trace row.
- Keep all paired runs and variants of a given task in a single partition unless a specific paired evaluation requires a clearly documented cross-condition comparison.
- Keep attack-template families or injection-task IDs held out for a robustness test.
- Keep the benign calibration set disjoint from train, validation, and final test in task identity.
- Run an explicit cross-agent experiment: train/tune on agent models A and B, test on C, while respecting the chosen calibration protocol.
- If using synthetic benign training tasks, execute and validate them in the same environment, separate them from final benchmark tasks, and report results with and without them.
- Do not use external/OOD results to select the model, threshold, features, or hyperparameters.
- Store split IDs in versioned files and hash them. Do not regenerate random splits casually between runs.

### 7.9 Small-data warning

AgentDojo has a limited task inventory compared with large standard ML datasets. Multiple attacks and repeated runs over the same user task do not create the same number of independent samples as unique tasks. This constrains training of a high-capacity model and makes narrow confidence intervals difficult.

Start with small models and strong baselines. If the independent task count is insufficient for reliable calibration or generalization claims, narrow the research questions rather than inflate the sample size by counting dependent steps as independent samples.

---

## 8. Model and feature specification

### 8.1 Model hierarchy: simplest first

Implement in this order:

1. Deterministic trace parser and data-quality reports.
2. Tool-transition Markov-chain baseline.
3. Pooled embedding anomaly baselines.
4. Content-only prompt-injection detector adapter.
5. Unconditioned causal sequence baseline.
6. Goal-conditioned sequence monitor.
7. Argument-provenance ablation.
8. Benign-only vs weakly supervised vs supervised-oracle comparison.
9. Optional graph model only if a defined ablation question and enough time remain.

Do not start with a GAT, custom graph schema, or several stacked risk scores. The graph is not a core requirement; trajectories are often short and close to a chain. It may be tested only as an ablation after the sequence baseline is correct.

### 8.2 Canonical step representation

A trajectory is `x = (s_1, ..., s_T)` with each step holding a tool call and tool output. At the pre-execution gate for proposed call `a_t`, the inference input is:

`u_t = (g, (a_1, o_1), ..., (a_{t-1}, o_{t-1}), a_t, metadata)`

where:

- `g`: trusted user goal;
- `a_i`: executed prior call;
- `o_i`: prior tool output;
- `a_t`: the current proposed call, not yet executed;
- `metadata`: documented trust and tool-risk policy features;
- no `o_t`, future step, final label, or future outcome is available.

The online scoring function must accept a `PreExecutionEvent` type rather than a fully completed trace. This structural separation reduces accidental leakage.

### 8.3 Text encoding

Candidate starting point: a frozen sentence encoder such as `sentence-transformers/all-MiniLM-L6-v2`, or another encoder selected and documented during the pilot. Verify its license, installed version, model revision, maximum sequence length, and local/runtime availability before choosing it.

- Split long tool observations into chunks compatible with the encoder's real maximum input length.
- Test `max` pooling versus mean pooling across chunk embeddings. Max pooling may preserve a short anomalous span; this is a hypothesis, not a guaranteed benefit.
- Store the encoder name, model revision/hash, chunk size, overlap, pooling strategy, and preprocessing settings in every run manifest.
- Do not use an LLM to normalize prose in the initial implementation. A normalizer may destroy attacker/benign distinctions and complicate reproducibility.
- Keep thought/reasoning content optional, and report the primary result without it.

### 8.4 Structured tool-call features

Serialize tool identity and arguments deterministically, for example `send_email(to=..., subject=..., body=...)`; retain the structured fields separately from the serialized text.

Features may include:

- tool name and tool category;
- argument key/value types;
- counts of arguments and entity types;
- value lengths and simple string/entity indicators;
- whether argument values appear in the goal or previously trusted context;
- whether values first appear in a documented untrusted observation;
- whether a new high-impact argument (recipient, account number, URL, path, amount, or similarly sensitive value) comes from untrusted content;
- prior tool transitions and step index/trajectory length.

Do not add sensitive-data extraction features that retain real credentials. In the benchmark use synthetic values and redact or hash where appropriate.

### 8.5 Goal-conditioned causal sequence model

Candidate model:

- A goal encoder `f_g(g)`.
- A per-step encoder that combines tool/argument features, prior observation embeddings, and optional provenance flags.
- A **causal** GRU or small causal Transformer that encodes only the allowed prefix and current proposed action into `h_t`.
- A goal–prefix compatibility score `c_t = cosine(f_g(g), h_t)` after projection into a shared dimension.
- Risk score `R_t = -c_t` or a learned score trained solely on allowed training labels/data.

Train an unconditioned sequence model as an ablation. Keep model size small and report parameter count, training time, and inference latency. The goal-conditioned score is only a hypothesis: it may flag legitimate early steps because the complete goal has not yet been realized. Calibration and same-suite hard negatives are especially important.

### 8.6 Training objective

A possible benign-only training objective is contrastive goal–prefix matching:

`score(i, j, t) = cosine(f_g(g_j), h_(i,t)) / temperature`

The correct pairing is goal `g_i` with its own benign trajectory prefix; negative goals must include other goals from the **same suite** where possible. Otherwise the model may recognize suite/domain vocabulary rather than task-goal alignment.

A standard in-batch contrastive cross-entropy can be used, but document:

- how positive pairs are formed;
- how negative goals are selected;
- how partial prefixes are sampled;
- how short prefixes and incomplete tasks are handled;
- what is trained/frozen;
- how classes and task identities are separated;
- whether synthetic tasks are used.

Do not claim the loss itself is novel. Do not tune any parameter using final test data.

Optional alternatives, only after baseline success:

- sequence reconstruction term as a comparison with Trajectory Guard-style systems;
- weak supervision using a small labeled training subset;
- supervised trajectory/step detector as an upper-bound reference.

### 8.7 Argument provenance features

For every argument value `v` in a proposed action, derive deterministic features from trace provenance and suite-specific trust rules:

- `in_goal(v)`: value appears in the user goal under a documented normalization policy;
- `in_trusted_context(v)`: value appears in a trust-approved context;
- `first_seen_in_untrusted_obs(v)`: first recorded appearance is in an untrusted tool output;
- `entity_type(v)`: URL, email, file path, amount, account-like identifier, or other—only as relevant to the synthetic benchmark schema;
- `is_new_entity(v)`: value did not appear in the goal or trusted context;
- `high_impact_tool`: policy tag for actions such as send, pay, delete, or share;
- `high_impact_untrusted_argument`: high-impact call whose relevant argument first appeared in an untrusted observation.

Define tool-risk tags and trust sources **before looking at final test results**. Keep the rules in configuration and test them. Provenance by exact lexical match will miss paraphrases, transformations, encoded values, computed values, and some legitimate values from untrusted sources. Test these limitations instead of calling the feature complete taint tracking.

### 8.8 Features that are exploratory only

Do not include the following in the main model without prior evidence and a successful ablation:

- GAT / heterogeneous graph representation;
- cosine distance between hidden reasoning and action text;
- action “velocity” or semantic drift;
- chain-of-thought dependence;
- causal influence inferred from attention weights;
- unverified semantic taint decay;
- hand-tuned fixed thresholds.

If an exploratory feature does not add measurable value, drop it and report that result as appropriate.

---

## 9. Calibration and decision policy

### 9.1 Why calibration matters

A per-step false-positive rate is not the same as the probability of interrupting a full benign trajectory. If the monitor checks many steps, a low per-step alarm probability can still create a high chance that at least one step is flagged. Therefore, the primary false-alarm quantity is **per trajectory**.

### 9.2 Calibration protocol

1. Fit encoders, models, feature normalization, and hyperparameters using training and validation only.
2. Freeze the chosen scoring function and all preprocessing.
3. Run the frozen scorer over a **separate benign calibration set**.
4. For each benign calibration trajectory `i`, compute its maximum prefix score `M_i = max_t z_(i,t)`, where `z_t` is either the raw score or a predeclared normalized score.
5. Select the conformal threshold using the prescribed order statistic.
6. Freeze the threshold before the final test.
7. Evaluate false-alarm rate and detection on the untouched test set.

Do not select the model or tune normalization using the calibration set if you intend to rely on the basic split-conformal finite-sample claim. Use validation for model choice; use calibration only for the threshold.

### 9.3 Basic per-trajectory conformal threshold

Let `M_1, ..., M_n` be maximum scores from `n` benign calibration trajectories. For target FPR `alpha`, sort the scores. A conservative threshold is the order statistic at:

`k = ceil((n + 1) * (1 - alpha))`

If `k <= n`, use the `k`-th smallest calibration score and flag a new trajectory at the first prefix where `z_t > threshold`. If `k = n + 1`, use an infinite threshold (no finite threshold can support that tail level from the available calibration sample under this rule).

This provides **marginal finite-sample coverage only under exchangeability** of the calibration and future benign trajectories. It does not guarantee the same FPR for each task, suite, model, or shifted distribution. If calibration trajectories are strongly dependent because they repeatedly reuse a small set of tasks, the nominal guarantee may not apply as assumed. Use task-disjoint splits and be explicit about the unit of exchangeability.

A useful resolution check: the smallest nonzero conformal tail probability is about `1/(n+1)`. A target near 5% needs at least about 19 exchangeable calibration units to resolve that tail; 1% needs about 99. More is preferable. These are mathematical resolution minima, not assurances of adequate power or generalization.

### 9.4 Length and shift considerations

The maximum score tends to depend on the number of decisions. Begin by calibrating the maximum across the full trajectory: this naturally targets the trajectory-level event, provided calibration and test trajectory-length distributions are comparable. Then test these alternatives only as planned ablations:

- raw score versus normalization using training-set step statistics;
- length-stratified calibration only if each stratum has enough independent calibration units;
- cross-task/cross-agent empirical false-alarm rate;
- explicit trajectory-length distribution reporting.

Do not split into many small bins solely to make a target FPR look better. A small calibration set cannot support many reliable conditional guarantees.

### 9.5 Decisions and operational modes

For the first implementation, use a clear interface such as:

- `ALLOW`: risk score is below the frozen threshold;
- `FLAG`: record an alert in detect-only mode;
- `HOLD`: pause a proposed action for controlled confirmation in the experimental policy;
- `BLOCK`: do not execute a proposed call in the experimental policy.

The score is **not a probability of maliciousness** unless the method has a separately defined and validated probabilistic interpretation. Do not display it as “X% chance of attack.”

### 9.6 Calibration reporting

Report for each calibration alpha:

- calibration unit and number of units;
- threshold and score definition;
- in-distribution test FPR with confidence interval;
- FPR by suite, trajectory length, and agent model where sample size supports it;
- FPR under each shift/adaptive condition;
- detection rate at the same operating point;
- cases where the nominal calibration assumption is visibly violated.

---

## 10. Benchmarks and experimental conditions

### 10.1 Main benchmark: AgentDojo

AgentDojo is the primary environment because it provides tool-using agent tasks and prompt-injection evaluations with environment-level outcomes. Its package and APIs may evolve, so do not install “latest” unpinned and assume reproducibility.

At the beginning of the project:

1. Inspect the official repository, docs, release tags, and license.
2. Decide whether to install a package release or check out a tagged Git commit.
3. Record both the code version and the task/data revision actually used. Do not confuse a task-set version mentioned in a paper with the Python package version.
4. Run the official quickstart and inspect the supported provider/model adapters.
5. Reproduce a minimal no-defense run and an attack run before designing the monitor integration.
6. Record exact environment variables and any model/API settings without logging secrets.
7. Save the source commit, dependency lock, commands, stdout/stderr, outcome checks, and cost.

### 10.2 Agent models

Target a minimum feasible set spanning agent behavior, not just many model names:

- At least one local/open-weight model if hardware permits.
- At least one hosted model if API budget and terms permit.
- A third model/version for a cross-agent test if feasible.

Choose exact models during the pilot based on AgentDojo compatibility, cost, repeatability, rate limits, and license. Pin exact model/version identifiers and parameters. Results apply only to those versions and task settings; do not claim universal model generalization.

### 10.3 Attack conditions

- **L0 — standard:** the benchmark's native/default injection templates.
- **L1 — held-out template:** alternative/paraphrased templates kept entirely outside training and validation.
- **L2 — adaptive:** an attack generation/optimization method targets the agent/defense under a recorded query/compute budget.
- **Optional L3 — mimicry:** malicious intent is distributed across individually benign-looking steps. Treat this as future work unless there is enough time and an operational definition.

For every condition, record whether the injection was actually exposed. A configured attack that never reached the agent is not equivalent to a detector successfully stopping an attack.

### 10.4 Required experimental conditions

At minimum, evaluate:

1. benign tasks with no attack;
2. attack-configured but unexposed runs;
3. exposed-but-resisted runs;
4. successful hijack runs;
5. held-out attack template families;
6. task-disjoint test data;
7. cross-agent condition;
8. one out-of-distribution benchmark or condition if feasible;
9. adaptive attack condition if feasible;
10. no-defense, detect-only, and in-loop monitor intervention conditions.

### 10.5 Two evaluation tracks

**Track 1 — Offline prefix replay:** feed each pre-execution event to the frozen monitor and measure whether it could have flagged before the harmful call. This evaluates detection without changing the trajectory.

**Track 2 — Closed-loop intervention:** integrate the monitor so a flagged call is held/blocked and the agent/environment continues according to a documented policy. Measure actual end-to-end ASR and benign utility.

Report these tracks separately. Offline TPR is not evidence that the monitor reduced ASR in the live loop.

---

## 11. Baselines and fair comparisons

Priority A baselines come first. Priority B are included only after their paper, code, license, and reproduction feasibility have been checked.

### 11.1 Priority A

**B1 — Tool-name transition baseline**

- Model tool-name transitions (for example first-order transition probabilities) on benign training traces.
- Score unusual tool sequences or transitions.
- Call it a simple transition baseline, not “ProbGuard,” unless the actual ProbGuard algorithm is faithfully implemented in its appropriate domain. ProbGuard is related work, not automatically a valid IPI comparator.

**B2 — Pooled-embedding anomaly baselines**

- Aggregate trajectory/step embeddings using a fixed, documented pooling rule.
- Evaluate Isolation Forest, One-Class SVM, and/or Mahalanobis distance trained on benign data.
- Fit all transformations only on the training split.
- Report how trajectories of different lengths are pooled.

**B3 — Content-only injection classifier**

- Run a public detector such as Meta Prompt Guard 2 or a benchmark-provided detector on untrusted observations/chunks.
- Use the model's documented interface and correct chunk/windowing behavior.
- Calibrate its decision on validation/calibration data if allowed by the comparison protocol.
- This baseline helps answer whether trajectory context adds value beyond classifying suspicious text. A content classifier detects suspicious content, not necessarily a successful hijack.

**B4 — Unconditioned causal sequence model**

- Match the proposed model's architecture and training budget while removing goal conditioning.
- This is the clean test of H2.

**B5 — Closest trajectory-monitor comparator**

- Reproduce Trajectory Guard if feasible and permitted by its license/instructions.
- If a faithful reproduction is impossible, document why and label any simplified version as a *reimplementation/proxy*, not the original method.

**B6 — Supervised trajectory detector/oracle**

- Train a small trajectory-level classifier using allowed labeled training traces.
- Keep a strict task-disjoint split and freeze the test set.
- The purpose is to estimate the value of supervision; it is not a fair replacement for the benign-only model if it uses labels the latter is denied.

### 11.2 Priority B, as feasible

- Zero-shot LLM judge over a pre-execution prefix, with fixed prompt/version and temperature settings.
- LlamaFirewall AlignmentCheck/Prompt Guard components, as applicable.
- AgentSentry if a fair, reproducible version is available.
- MELON if its setup is feasible and its behavior can be matched to the benchmark.
- An applicable minimize-and-sanitize/enforcement-based defense. This is essential to establish whether a monitor adds value over a simpler control.
- Graph-based detector only as an ablation after causal sequence baselines work.

### 11.3 Rules for fair comparisons

- Compare on the same held-out trajectories whenever possible.
- Use the same attack conditions and label rules.
- Do not compare scores reported by separate papers as though they came from the same test set.
- State differences in tool access, model access, runtime intervention, context visibility, and compute budget.
- Include the closest direct competitors first; do not choose only weak baselines.
- Report reproduction deviations and failures.
- When an external implementation cannot run, do not invent its expected score. Report the limitation and use an appropriately labeled proxy or omit it with justification.

---

## 12. Metrics and statistical analysis

### 12.1 Primary detection metrics

Let `R_t` be the risk score for the proposed call at decision step `t` and `tau` the frozen threshold.

**Pre-execution true-positive rate**

`TPR_pre(tau) = P(first flag occurs at t <= t_harm | trajectory label = HIJACKED)`

A flag after the harmful call executes does not count as a successful pre-execution detection.

**Per-trajectory false-positive rate**

`FPR_traj(tau) = P(at least one flag anywhere in the trajectory | BENIGN)`

Report the same rate for `UNEXPOSED` separately, and report the rate on `EXPOSED_RESISTED` separately. Avoid hiding this group inside either “benign” or “attacked” without explaining the interpretation.

**Detection lead time**

`lead_time = t_harm - t_first_flag`

Report the distribution among correctly pre-flagged hijacks. State that the count is in tool-decision steps; do not call it seconds unless wall-clock time is measured.

### 12.2 Secondary metrics

- AUROC.
- AUPRC, always accompanied by class prevalence and test-set counts.
- Precision, recall, F1 at specified operating points.
- End-to-end ASR after intervention.
- Benign task completion/utility and benign interruption rate.
- Cost per run and wall-clock latency per decision.
- Runtime/compute overhead relative to the agent call, on named hardware.
- Score/threshold drift across suites, models, trajectory lengths, and attack types.
- Error breakdown: false flags, missed hijacks, late flags, label ambiguity, exposed-but-resisted, and unexposed.

### 12.3 Statistical uncertainty

- Use at least three random seeds for learned models if compute budget permits.
- Use paired comparisons on the same task/configuration instances where the design supports pairing.
- Use a task-clustered bootstrap for confidence intervals so multiple trajectories from the same user task are not treated as fully independent observations.
- Report point estimates, 95% confidence intervals, denominator counts, number of unique tasks, and number of runs.
- For small counts, consider exact/binomial intervals for simple rates in addition to the bootstrap; explain the choice.
- Predeclare one primary metric and clearly identify secondary/exploratory analyses.
- Correctly describe uncertainty. A CI that includes zero is not evidence of an effect; a difference with a narrow CI can still be practically insignificant.
- Do not report only the best seed or the best attack template.

### 12.4 In-loop evaluation

For each task/attack instance, run paired conditions where feasible:

1. no defense;
2. monitor in detect-only mode;
3. monitor with the frozen hold/block policy;
4. strongest feasible baseline defense.

Measure actual security and utility outcomes in each condition. Holding a call may lead to a different plan; that is part of the intervention effect. Record follow-up behavior and whether the agent eventually performs a harmful action by another route.

### 12.5 Cost reporting

Record:

- model/provider and exact versions;
- local hardware (CPU, GPU, RAM) and software runtime versions;
- number of agent calls, monitor calls, retries, and adaptive attack queries;
- wall-clock runtime and latency percentiles;
- estimated API cost with the rate source/date if applicable;
- cache behavior and reuse of identical traces.

Do not promise a latency target such as “under 80 ms” before measurement. Report it as an empirical result under defined hardware and workload only.

### 12.6 Plots to produce

- Detection ROC and precision–recall curves with prevalence noted.
- `TPR_pre` vs `FPR_traj` operating-point plot.
- End-to-end ASR vs benign task completion/utility.
- Calibration FPR by agent, suite, and trajectory-length group, when sample size permits.
- Detection lead-time distribution.
- Adaptive-attack degradation curves under a declared query budget.
- Ablation plot/table for goal conditioning, provenance, thoughts, pooling, and sequence architecture.
- Error analysis table with the most common failure categories.

Every plot must be generated from the frozen results registry or raw result files by a script. Do not edit plotted numbers manually.

---

## 13. Implementation plan and repository structure

### 13.1 Recommended repository layout

```text
agentwatch-a/
├── AGENTWATCH_DIRECTION_A_SPEC.md
├── README.md
├── AGENTS.md                         # concise rules for Antigravity
├── pyproject.toml
├── requirements.lock                 # or a committed lock produced by the chosen tool
├── .python-version                   # if supported by the chosen environment tool
├── .gitignore
├── .env.example                      # names/placeholders only; never real secrets
├── config/
│   ├── default.yaml
│   ├── benchmark_agentdojo.yaml
│   ├── model_goal_conditioned.yaml
│   └── evaluation.yaml
├── research/
│   ├── literature_matrix.csv
│   ├── novelty_matrix.csv
│   ├── research_questions.md
│   ├── analysis_plan.md
│   ├── decision_log.md
│   ├── threat_model.md
│   └── limitations.md
├── data/
│   ├── README.md                     # data sources, licenses, schema, instructions
│   ├── raw/.gitkeep                  # usually ignored by Git
│   ├── processed/.gitkeep            # usually ignored by Git
│   ├── splits/.gitkeep
│   └── sample_traces/                # tiny synthetic examples only
├── src/agentwatch_a/
│   ├── __init__.py
│   ├── cli.py
│   ├── settings.py
│   ├── schemas.py
│   ├── provenance.py
│   ├── trace_store.py
│   ├── benchmark/
│   │   ├── __init__.py
│   │   ├── agentdojo_adapter.py
│   │   └── version_check.py
│   ├── features/
│   │   ├── __init__.py
│   │   ├── text_embeddings.py
│   │   ├── action_features.py
│   │   └── trajectory_features.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── interface.py
│   │   ├── transition_baseline.py
│   │   ├── embedding_baselines.py
│   │   ├── content_detector.py
│   │   ├── sequence_baseline.py
│   │   └── goal_conditioned.py
│   ├── calibration/
│   │   ├── __init__.py
│   │   └── conformal.py
│   ├── policy/
│   │   ├── __init__.py
│   │   └── decisions.py
│   ├── evaluation/
│   │   ├── __init__.py
│   │   ├── metrics.py
│   │   ├── statistics.py
│   │   ├── ablations.py
│   │   └── error_analysis.py
│   └── reporting/
│       ├── __init__.py
│       ├── tables.py
│       └── plots.py
├── scripts/
│   ├── verify_environment.py
│   ├── run_pilot.py
│   ├── generate_traces.py
│   ├── validate_traces.py
│   ├── create_splits.py
│   ├── train_baselines.py
│   ├── train_monitor.py
│   ├── calibrate_monitor.py
│   ├── evaluate_offline.py
│   ├── evaluate_in_loop.py
│   └── build_report.py
├── tests/
│   ├── unit/
│   │   ├── test_schemas.py
│   │   ├── test_no_future_leakage.py
│   │   ├── test_provenance.py
│   │   ├── test_conformal.py
│   │   └── test_metrics.py
│   ├── integration/
│   │   ├── test_trace_roundtrip.py
│   │   └── test_agentdojo_smoke.py
│   └── fixtures/
│       └── tiny_synthetic_traces.jsonl
├── runs/                             # generated outputs; ignored by Git
├── reports/                          # generated reports; keep source scripts
└── docs/
    ├── trace_schema.md
    ├── benchmark_setup.md
    └── reproduction.md
```

The layout is a target architecture, not a requirement to create every empty file on day one. Build modules incrementally and avoid unnecessary abstractions.

### 13.2 Suggested command-line interface

Use a single CLI with clear, reproducible commands. Exact syntax may vary, but cover these actions:

```text
agentwatch doctor
agentwatch benchmark-check --config config/benchmark_agentdojo.yaml
agentwatch pilot --config config/benchmark_agentdojo.yaml
agentwatch traces validate --input data/raw/<trace_file>.jsonl
agentwatch splits create --config config/evaluation.yaml
agentwatch baselines train --config config/default.yaml
agentwatch monitor train --config config/model_goal_conditioned.yaml
agentwatch calibrate --config config/evaluation.yaml --alpha 0.05
agentwatch evaluate offline --config config/evaluation.yaml
agentwatch evaluate in-loop --config config/evaluation.yaml
agentwatch report --run-id <run_id>
```

The CLI must fail with actionable errors if a required version, path, model, API key, or output directory is missing. It must not silently fall back to an unpinned latest package or unrecorded default settings.

### 13.3 Dependency policy

Choose a Python 3.11 environment as the initial compatibility target unless benchmark/provider verification identifies a reason to use another supported version. AgentDojo's public package metadata indicates Python 3.10+ support; nevertheless, test the chosen exact version with the pinned release before adopting it.

Initial dependency categories:

- scientific/data: `numpy`, `pandas`, `scipy`, `scikit-learn`;
- deep learning and embeddings: `torch`, `sentence-transformers`, `transformers` only as required;
- schema/config/CLI: `pydantic`, `pyyaml`, `typer`, `rich`;
- test/style/type checking: `pytest`, `pytest-cov`, `ruff`, optionally `mypy`;
- plots: `matplotlib`;
- benchmark dependency: pinned AgentDojo source/package and only the extras needed for the selected provider.

Do not install every possible agent framework. Do not add LangChain, LangGraph, a database, a vector database, FastAPI, or a dashboard unless a documented research need appears. This is an experimental research system, not a production SaaS project.

Record exact versions in a lock file after compatibility tests pass. Do not put loose package versions in the final reproducibility instructions and claim a pinned environment.

---

## 14. Python environment and sandbox setup

### 14.1 Important security distinction

A Python virtual environment (`.venv`) isolates Python packages. **It is not a security sandbox**: code running inside it can generally still access the same files, processes, and network as the user. For downloaded benchmark code or autonomous coding-agent commands, use an OS/container/VM boundary in addition to the virtual environment.

Use three layers:

1. **Project boundary:** open only the project directory in Antigravity and Git.
2. **Python environment:** `.venv` with locked dependencies.
3. **Command sandbox:** Antigravity's terminal sandbox where available; otherwise a restricted Docker/WSL2/VM environment. Do not rely on `.venv` alone.

### 14.2 Windows PowerShell setup

Open a terminal in the desired parent directory. Create the project folder and enter it:

```powershell
mkdir agentwatch-a
cd agentwatch-a
git init
```

Check installed Python versions:

```powershell
py -0p
py -3.11 --version
```

If Python 3.11 is not installed, install a supported Python 3.11 release from the official Python site, then reopen the terminal. Do not uninstall another working Python version solely for this project.

Create and activate the virtual environment:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python --version
python -m pip install --upgrade pip wheel
```

If PowerShell blocks activation, first use the current-session-only option below rather than changing the machine-wide execution policy:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

An alternative that avoids activation is:

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip wheel
.\.venv\Scripts\python.exe -m pytest
```

Confirm that the Python executable points inside the project:

```powershell
python -c "import sys; print(sys.executable)"
```

Expected path should include `agentwatch-a\.venv\`.

### 14.3 Linux/macOS shell setup

```bash
mkdir agentwatch-a && cd agentwatch-a
git init
python3.11 -m venv .venv
source .venv/bin/activate
python --version
python -m pip install --upgrade pip wheel
python -c 'import sys; print(sys.executable)'
```

### 14.4 `.gitignore` minimum

Create `.gitignore` before generating traces or installing models:

```gitignore
# Python
.venv/
__pycache__/
*.py[cod]
.pytest_cache/
.mypy_cache/
.ruff_cache/
.coverage
htmlcov/

# Secrets
.env
.env.*
!.env.example
*.pem
*.key

# Local datasets, generated traces, model artifacts
/data/raw/**
/data/processed/**
/runs/
/checkpoints/
/models/
*.pt
*.pth
*.safetensors

# IDE and OS files
.vscode/
.idea/
.DS_Store
Thumbs.db
```

If a small subset of synthetic traces is safe and useful for tests, explicitly add it under `tests/fixtures/` and make sure it contains no secrets or licensed data that cannot be redistributed. Do not broadly force-add raw data to Git.

### 14.5 Environment variables and secrets

Create `.env.example` with variable names and placeholders only. Example:

```dotenv
# Fill locally; never commit real secrets.
OPENAI_API_KEY=
GOOGLE_API_KEY=
ANTHROPIC_API_KEY=
HF_TOKEN=
AGENTWATCH_DATA_DIR=./data
AGENTWATCH_RUNS_DIR=./runs
```

Use only the variables required by the selected provider. Do not log secrets. Validate required environment variables at startup and report only whether a key is configured—not its value.

### 14.6 Install the project after the package skeleton exists

After `pyproject.toml` defines project metadata and dependencies:

```powershell
python -m pip install -e ".[dev]"
python -m pytest
python -m ruff check .
```

Lock dependencies using one chosen tool consistently. If using pip, record a tested fully pinned requirements/constraints file; if using `uv`, commit its lock file and use locked/sync commands. Do not maintain multiple contradictory lock files.

### 14.7 AgentDojo install strategy

Do not begin with an unpinned `pip install -U agentdojo` for final experiments. First inspect the official repository and the supported version/tags. Then either:

- install an exact package release confirmed to match the needed task revision; or
- clone the official repository and checkout the exact audited commit/tag.

Record the resolved commit SHA, package metadata, benchmark/task revision, Python version, and all transitive dependency versions. Run the upstream quickstart and save the output. Its API may change, so isolate imports behind `src/agentwatch_a/benchmark/agentdojo_adapter.py` instead of allowing upstream objects to leak through the entire codebase.

### 14.8 Antigravity terminal sandbox

Use the current official [Antigravity sandbox documentation](https://antigravity.google/docs/sandbox/) and settings docs, because menu names and supported OS versions can change.

Recommended configuration:

- Enable **Terminal Sandbox** for the project where supported.
- Keep terminal command execution on **Request Review** during initial setup; if the platform offers “Proceed in Sandbox,” use it only while the sandbox is enabled and you understand its limits.
- Keep non-workspace file access disabled.
- Keep strict/review-oriented permissions for browser/MCP actions where available.
- Restrict network access to the domains required for package installs and model downloads; disable network for tests that do not need it.
- Never switch to “Always Proceed” simply to make installation faster.

Windows support and behavior depend on the Antigravity version and Windows build. Official documentation has described sandbox support as requiring Windows 11 24H2 or later with a specified update; verify this in the current docs and in the UI. If unavailable, use Docker/WSL2 or a separate VM as the OS-level boundary.

### 14.9 Optional Docker sandbox for risky/untrusted commands

If Docker is available, run benchmark/model experiments in a container with:

- only the repository and required data directories mounted;
- no home directory, SSH keys, browser profiles, or unrelated drives mounted;
- no privileged mode;
- non-root user if compatible;
- no network during pure tests, and restricted/approved network only for downloads or API-backed runs;
- resource limits where supported;
- simulated tools and synthetic data only.

A `venv` inside Docker may still be useful for dependency consistency, but the container—not the `venv`—provides OS-level isolation. A container is not a perfect security boundary against all host/container vulnerabilities; do not run unknown code with secrets attached.

**Optional example `Dockerfile.dev`** (use only after `pyproject.toml`, `README.md`, and `src/` exist; build dependencies from a reviewed, pinned lock):

```dockerfile
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH"
RUN python -m venv /opt/venv \
    && useradd --create-home --uid 10001 runner
WORKDIR /workspace
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir -e ".[dev]" \
    && chown -R runner:runner /workspace /opt/venv
USER runner
CMD ["bash"]
```

Build during a reviewed dependency-install step (that needs registry access):

```powershell
docker build -f Dockerfile.dev -t agentwatch-a:dev .
```

Then use the built image for offline tests with no network, limited resources, no extra Linux capabilities, and only the project folder mounted. In PowerShell:

```powershell
$workspace = (Get-Location).Path
docker run --rm -it --network none `
  --cap-drop=ALL --security-opt no-new-privileges `
  --pids-limit 256 --memory 8g --cpus 4 `
  --mount "type=bind,source=$workspace,target=/workspace" `
  --workdir /workspace agentwatch-a:dev bash
```

This command intentionally disables networking; use it for local tests and offline analysis, not model/API calls or first-time downloads. If the source project needs to install dependencies, rebuild the reviewed image rather than opening broad network access inside the test container. Check the actual host resource budget before using the example `8g`/`4` limits. Keep `.env` outside the mount; never mount your home folder, SSH directory, or unrelated drives.

### 14.10 Environment validation command

Implement `agentwatch doctor` or `scripts/verify_environment.py` to print (without secrets):

- Python version and executable path;
- OS and architecture;
- project root and output/data paths;
- package versions and lock status;
- PyTorch version and whether CUDA is available;
- availability of the pinned sentence encoder/local cache;
- benchmark repository/package revision;
- required environment variables present/absent;
- whether raw data directories are ignored by Git;
- whether output directories are writable.

Exit nonzero for missing requirements rather than silently continuing.

---

## 15. Google Antigravity operating instructions

### 15.1 Use the specification as the source of truth

Open the `agentwatch-a` repository as the Antigravity workspace and put this specification in the repository root. Also create a concise `AGENTS.md` containing the rules in Section 15.2. Do not make Antigravity infer the project from a long chat alone.

### 15.2 Rules for the coding agent (`AGENTS.md`)

Use the following rules verbatim or summarize them without weakening them:

1. Follow `AGENTWATCH_DIRECTION_A_SPEC.md` as the project source of truth.
2. Work in small phases and stop at every go/no-go gate. Do not implement later phases without passing the current gate.
3. Before editing, inspect the existing code and propose a plan. Do not overwrite existing user files without explaining the change.
4. Never invent benchmark outputs, metrics, model availability, paper results, repository tags, or licenses.
5. Never access or print `.env` values, credentials, tokens, unrelated folders, or private files.
6. Never connect to real email, banking, cloud, GitHub, or production accounts. All tool-use tests must stay in the local simulated benchmark unless explicit authorization is provided.
7. Never call a proposed model action after its result has been added to the input. Enforce the pre-execution information boundary in types and tests.
8. Every experiment must save the exact config, split IDs, seeds, code commit, benchmark version, environment, logs, and raw metric output.
9. Do not tune on the final test set or use OOD results for threshold/model selection.
10. Do not label a simplified reimplementation as the original paper's model.
11. Do not claim that a monitor is novel merely because it combines known components.
12. Do not add a dashboard, database, API server, graph neural network, rollback system, or unrelated framework unless a research decision log justifies it.
13. Write tests for all score, calibration, label, and metric definitions before running large experiments.
14. Ask for review before running destructive commands, deleting/moving data, installing unfamiliar system dependencies, or executing long-running/expensive API-based experiments.
15. Preserve raw traces. Never silently modify a previous experiment's result file; create a new run ID.
16. Report failures and unsupported assumptions honestly. Stop if the benchmark's outcome semantics are unclear.

### 15.3 Suggested project workflow inside Antigravity

Use one task per stage:

- Stage 0: literature and novelty matrix.
- Stage 1: project skeleton and environment verification.
- Stage 2: AgentDojo adapter and minimal smoke test.
- Stage 3: trace schema and outcome/label audit.
- Stage 4: baseline implementation and reproduction.
- Stage 5: data split freeze and baseline report.
- Stage 6: monitor model implementation.
- Stage 7: conformal calibration and unit tests.
- Stage 8: held-out evaluation and ablations.
- Stage 9: adaptive/OOD and in-loop evaluation.
- Stage 10: result audit, paper figures, reproducibility package.

Do not ask Antigravity to “build the complete project in one go.” Large end-to-end coding requests encourage untested abstractions, implicit fallback behavior, fake results, and incomplete evaluation.

### 15.4 Human review requirements

The researcher—not the coding agent—must approve:

- the threat model and novelty claim;
- benchmark release/commit and data license;
- split policy and final test freeze;
- high-impact tool/provenance rules;
- primary metric and calibration target;
- expensive or adaptive attack runs;
- final claim wording and paper citations.

Antigravity can implement scripts and analyze saved data, but its generated literature summaries, labels, and statistical interpretations must be checked against primary sources and raw outputs.

---

## 16. Configuration, reproducibility, and experiment tracking

### 16.1 Configuration-first design

Store all experiment choices in YAML/JSON configs. Avoid hardcoding model names, thresholds, seeds, dataset roots, attack options, or tool-risk policy inside modules.

Example `config/default.yaml` (illustrative; replace placeholders after the pilot):

```yaml
project:
  name: agentwatch-a
  version: "0.1.0"
  seed: 17

paths:
  raw_data: ./data/raw
  processed_data: ./data/processed
  splits: ./data/splits
  runs: ./runs
  reports: ./reports

benchmark:
  name: agentdojo
  package_version: null       # fill only after verification
  repository_commit: null     # exact SHA required for final experiments
  task_revision: null         # record separately from package version
  suites: [workspace, slack, travel, banking]
  attack_levels: [L0, L1]

monitor:
  mode: detect_only
  primary_model: goal_conditioned_gru
  use_thought_text: false
  use_provenance: false        # add only after baseline gate
  embedding_model: null        # select and pin during pilot
  chunk_pooling: max
  max_observation_tokens: null # set from encoder metadata

calibration:
  method: split_conformal_max_score
  primary_alpha: 0.05
  secondary_alpha: 0.01
  score_normalization: raw     # alternative must be predeclared

splits:
  group_key: user_task_id
  hold_out_attack_templates: true
  hold_out_agent_for_cross_agent_test: true
  external_ood_benchmark: agentdyn

reproducibility:
  learned_model_seeds: [17, 29, 43]
  save_raw_scores: true
  save_split_ids: true
  save_code_commit: true
  save_environment_manifest: true
```

A config with unresolved `null` placeholders should fail final-run validation. It is fine for early drafts to be incomplete.

### 16.2 Experiment manifest

Each run directory should contain:

```text
runs/<run_id>/
  config.resolved.yaml
  environment.json
  git_commit.txt
  split_ids.json
  command.txt
  stdout.log
  stderr.log
  traces_or_trace_refs.jsonl
  scores.jsonl
  metrics.json
  summary.md
```

If raw data cannot be copied into the run folder for licensing/storage reasons, record a stable dataset revision and hashes/IDs instead.

### 16.3 Immutable run IDs

Use deterministic IDs derived from date/time plus config hash or a stable unique ID. A run ID must never point to multiple configurations. Never overwrite a completed run. Store failed runs as well as successful runs with a failure status so the analysis reflects actual experiment attempts.

### 16.4 Decision log

Every important decision must be written to `research/decision_log.md` with:

- date;
- question/decision;
- evidence reviewed;
- alternatives considered;
- reason selected;
- effect on hypotheses or scope;
- whether the analysis plan changed.

### 16.5 Data-management and licensing

Before collecting large-scale traces, document:

- dataset/benchmark license and attribution;
- whether external model output can be redistributed;
- whether generated traces contain copyrighted or sensitive material;
- data retention rules and storage requirements;
- which artifacts can be public and which must be recreated by the user.

Never claim to release a trace corpus until redistribution permissions have been checked.

---

## 17. Testing and quality requirements

### 17.1 Unit tests required before model training

**Schema tests**
- valid trace parses;
- missing run IDs, invalid labels, malformed calls, and incompatible versions fail clearly;
- nullable thought fields are supported;
- repeated step indices or malformed timestamps are detected;
- JSONL write/read round-trips preserve values.

**Pre-execution/no-future-leakage tests**
- the scorer input type cannot contain the current call's result;
- editing future observations does not change an earlier score;
- changing the final outcome label does not change the online score;
- no `t_harm`, `security_success`, or future data is passed to inference feature extraction;
- model score at step `t` depends only on the allowed goal/history/current-call fields.

**Provenance tests**
- exact value seen in untrusted output is tagged correctly;
- same value in trusted goal is not tagged as first appearing untrusted;
- entity normalization behavior is deterministic;
- benign value copied from a legitimate untrusted source is not automatically considered malicious;
- unknown tools default to documented conservative behavior, not implicit trust.

**Conformal tests**
- order statistic is correct on hand-worked score arrays;
- `k = n + 1` yields an infinite threshold;
- flags use the documented strict/non-strict comparison consistently;
- trajectory maximum, not average score, is used for trajectory-level calibration;
- calibration set data cannot enter model fitting;
- alpha, sample size, threshold, and calibration IDs are saved.

**Metric tests**
- flags after `t_harm` do not count as pre-execution TPs;
- false-alarm denominator uses the selected label groups explicitly;
- AUPRC report contains prevalence;
- task-level grouping is preserved by bootstrap code;
- empty/undefined metric cases return documented warnings rather than misleading zero values.

### 17.2 Integration tests

- tiny synthetic trace can be loaded, scored, calibrated, and evaluated end-to-end;
- small AgentDojo smoke test completes without real external side effects;
- no-defense and detect-only modes create comparable trace records;
- monitor holds/blocks a simulated call in the in-loop test;
- report-generation script reproduces metrics from saved raw score files;
- configuration and split hashes match the run manifest.

### 17.3 Code quality

- Type annotations for core schemas, scorers, and metric functions.
- `ruff` passes on the project.
- `pytest` passes on clean setup.
- Important modules have concise docstrings.
- Avoid broad exception handling that silently converts errors into benign scores.
- Any fallback behavior is explicit and logged.
- No secrets, local caches, raw trace dumps, or huge model files in Git.

### 17.4 Failure handling

A failed model/API call, malformed trace, missing outcome checker, or unavailable dependency must be recorded as a failed run—not converted into `BENIGN`, `UNEXPOSED`, or a zero risk score. The analysis must state how failed runs were treated and how many occurred.

---

## 18. Implementation phases and go/no-go gates

The timeline is relative. The exact calendar schedule depends on semester and conference deadlines.

### Phase 0 — Literature and novelty audit

**Tasks**
- Read the closest papers in Section 3.1 in full.
- Inspect official code/repositories and licenses.
- Fill `literature_matrix.csv` and `novelty_matrix.csv`.
- Write a one-page threat model and primary research question.
- Confirm that the proposed boundary, calibration unit, and evaluation protocol differ meaningfully from the closest work.

**Deliverable:** research-gap memo and scope freeze.

**Gate N0:** If no defensible gap remains, revise the question before implementing the model.

### Phase 1 — Environment and benchmark smoke test

**Tasks**
- Create `.venv`, lock dependencies, secure Antigravity/Docker environment.
- Pin AgentDojo package/commit and task revision.
- Run upstream quickstart.
- Choose the first agent model/provider.
- Execute a tiny benign and attack example.
- Verify outcomes and estimate time/API cost.

**Deliverable:** `docs/benchmark_setup.md`, environment manifest, run logs.

**Gate G0:** the benchmark runs, outcome labels are inspectable, and no-defense behavior is reproducible within a documented tolerance. If not, fix instrumentation before moving on.

### Phase 2 — Trace schema and label audit

**Tasks**
- Implement schema and JSONL store.
- Record pre-execution events separately from post-execution observations.
- Validate the four outcome labels.
- Write no-future-leakage tests.
- Audit trace labels and environment checkers.

**Deliverable:** a tiny validated trace corpus plus data-quality report.

**Gate G0.5:** no unresolved fatal label or temporal-leakage issue. If unclear whether a harmful call can be identified, re-scope the primary endpoint.

### Phase 3 — Core baselines

**Tasks**
- Implement B1 and B2.
- Add the content-only detector (B3) if its prerequisites are available.
- Implement the unconditioned causal sequence baseline (B4).
- Reproduce Trajectory Guard or document an exact feasibility blocker and a faithful proxy.
- Implement the supervised oracle (B6) only after the split and labels are valid.
- Save raw scores and all run manifests.

**Deliverable:** baseline report on a small held-out pilot split.

**Gate G1:** If the supervised oracle cannot distinguish HIJACKED from BENIGN better than chance under correct splits, investigate label quality, task counts, and available features. If only the supervised oracle succeeds, pivot to a weakly supervised or evaluation-led study. Do not blindly scale up.

### Phase 4 — Freeze the data protocol

**Tasks**
- Finalize task-disjoint train/validation/calibration/test IDs.
- Hold out attack templates for one test condition.
- Define cross-agent split.
- Freeze primary/secondary metrics and calibration targets.
- Save `analysis_plan.md` before full experiments.

**Deliverable:** immutable split files, checksums, analysis plan.

**Gate G1.5:** no leakage or ambiguous sample unit. If the benchmark cannot support enough independent calibration units, lower the ambition of the calibration claim or add validated data without contaminating the test set.

### Phase 5 — Proposed model (minimal version)

**Tasks**
- Implement frozen text encoder, current action features, and causal GRU.
- Implement goal conditioning and same-suite hard negatives.
- Train on allowed benign training data only for the primary benign-only model.
- Use validation only for hyperparameters/model selection.
- Compare with unconditioned sequence baseline.

**Deliverable:** versioned model, training config, checkpoints, validation report.

**Gate G2:** keep goal conditioning only if the matched ablation provides evidence of value or the resulting analysis still answers a useful question.

### Phase 6 — Provenance and conformal calibration

**Tasks**
- Add deterministic argument-provenance features behind a config flag.
- Run with/without provenance on identical splits.
- Freeze model and compute benign calibration trajectory maxima.
- Apply the conformal threshold and save calibration artifacts.
- Test finite-sample rank calculation and empirical FPR.

**Deliverable:** calibration report and provenance ablation.

**Gate G2.5:** If sample size or exchangeability is not defensible, report calibration as an empirical thresholding procedure without overstating a guarantee. If provenance adds no value, remove it from the core model.

### Phase 7 — Main held-out evaluation

**Tasks**
- Run the frozen test set once after all choices are frozen.
- Report TPR_pre at the selected FPR, AUROC/AUPRC, false interruptions, lead time, and uncertainty.
- Compare against strong baselines on the same test cases.
- Audit errors by suite, label class, tool, and failure type.

**Deliverable:** primary results table and error-analysis report.

**Gate G3:** The proposed model must either show an important, defensible benefit or the paper must pivot to a justified evaluation/negative result. Do not invent a new architecture just to beat a baseline.

### Phase 8 — Shift/adaptive/in-loop evaluation

**Tasks**
- Cross-agent evaluation.
- Held-out attack-template evaluation.
- AgentDyn or another external OOD condition if feasible.
- Adaptive attack condition with recorded budget if feasible.
- In-loop intervention versus no defense and strongest feasible alternative.

**Deliverable:** robustness, shift, latency, and utility reports.

**Gate G4:** If the monitor is dominated by a simpler enforcement defense, report it honestly and reconsider whether the monitor is best framed as an audit/triage layer.

### Phase 9 — Final result freeze and publication package

**Tasks**
- Freeze raw data, result registry, configs, code commit, and paper figures.
- Re-run report generation from saved outputs.
- Verify every number in the draft against machine-readable results.
- Review related work and citations again.
- Write limitations and data/license statements.
- Prepare anonymous submission artifact if applicable.

**Deliverable:** reproducibility package and submission-ready draft.

### Suggested overall schedule

| Relative period | Focus | Output |
|---|---|---|
| Week 1 | Literature/numerical audit + benchmark feasibility | Novelty memo, environment ready |
| Weeks 2–3 | Adapter, schema, trace generation, label audit | Validated trace corpus v1 |
| Week 4 | Baselines and data-split freeze | Baseline and leakage report |
| Weeks 5–6 | Minimal causal/goal-conditioned model | Model v1, ablations |
| Week 7 | Provenance and calibration | Calibration report |
| Weeks 8–9 | Held-out, cross-agent, OOD/adaptive, in-loop | Main findings |
| Weeks 10–11 | Statistics, error analysis, figures, writing | Complete paper draft |
| Week 12 | Reproduction pass and submission buffer | Submission/artifact package |

This schedule is ambitious. Prefer a smaller complete study with fair comparisons over a large, partially working system. Conference dates must be checked independently; this timeline is not a promise of acceptance or submission to a particular venue.

---

## 19. Risk register and fallback plan

| Risk | Early signal | Mitigation/fallback |
|---|---|---|
| Novelty overlaps prior work | Closest method already uses the same input, model objective, and evaluation. | Narrow to a testable online/calibration/adaptive question or pivot before implementation scales. |
| Task count too small | Same few user tasks appear repeatedly; wide uncertainty. | Reduce model capacity; split by task; use only validated extra tasks for training; state limitations; avoid broad generalization claims. |
| Label checker is unreliable | Manual review disagrees with outcome labels. | Fix/audit checker; exclude only under preregistered rules; document every change. |
| Temporal leakage | Score changes when future observations/labels are modified. | Stop; correct event boundary and add adversarial unit tests. |
| Model detects attack wording only | Performance collapses on held-out templates or content-only baseline matches it. | Expand held-out-template tests, add same-suite benign hard negatives, or pivot to an honest evaluation result. |
| Goal encoder learns suite/domain | Cross-suite/within-suite diagnostics reveal shortcut. | Same-suite hard negatives, task-disjoint splits, simpler baseline, feature audits. |
| Conformal guarantee overstated | Small calibration set, repeated tasks, task/model shift. | Use correct calibration unit, show sample resolution, report empirical shift FPR, narrow guarantee language. |
| Content classifier baseline is weak/outdated | Detector version has changed or runs with incorrect chunking. | Pin model revision, correct windowing, describe version, add stronger feasible comparator. |
| Enforcement defense dominates monitor | ASR lower and utility equal/better for simpler defense. | Reframe the monitor as detection/audit/forensics only if it has demonstrated value there; otherwise report the finding and pivot. |
| Agent/provider cost or API failures | Rate limit, model version drift, high per-run cost. | Pilot costs first, prefer local models for volume, cache reusable outputs, record failures and versions. |
| AgentWatch name collision | Public repository/project already uses similar name. | Keep internal code name but choose a distinctive repository/paper name before release. |
| Antigravity executes too much autonomously | Large changes, silent dependency drift, unreviewed installs. | Use small phases, request review, terminal sandbox, Git commits, and explicit gates. |
| No model win | Proposed model does not beat simple or strong baselines. | Do not add arbitrary layers; investigate feature contribution and whether the evaluation itself reveals an important failure mode. |

### Fallback paper concept

If the proposed model is not superior, a fallback study may be framed as:

> A rigorous evaluation of the reliability limits of black-box online monitors for agent prompt injection, comparing benign-only and supervised methods under outcome-based labels, task/model shift, and adaptive attacks.

This is only publishable if the protocol, dataset, comparisons, or findings are independently valuable. “Our model did not work” alone is not a paper contribution.

---

## 20. Paper and artifact plan

### 20.1 Proposed paper structure

1. **Abstract:** problem, method/protocol, main measured results, limitations. Write last.
2. **Introduction:** security problem, why the online pre-execution setting matters, what existing work establishes, the precise unresolved question, contributions.
3. **Related work:** trajectory monitors, IPI defenses, runtime guards, conformal anomaly detection, benchmarks/adaptive attacks.
4. **Threat model:** attacker capabilities, trusted/untrusted channels, intervention point, assumptions and out-of-scope threats.
5. **Problem formulation:** trace prefix, proposed call, outcome labels, TPR_pre, FPR_traj, utility/ASR.
6. **Method:** trace features, model, training protocol, provenance features, calibration rule.
7. **Experimental setup:** benchmarks, exact versions, agent models, splits, baselines, seeds, budget, statistics.
8. **Results:** primary outcomes first; then shift, adaptive attack, in-loop utility, latency, and ablations.
9. **Failure analysis:** false alarms, late detections, missed hijacks, label ambiguity, distribution shift.
10. **Limitations and ethics:** sample size, model coverage, benchmark validity, exchangeability, monitor attack surface, costs, reproducibility constraints.
11. **Conclusion:** only the claims supported by evidence.
12. **Appendix/artifact:** configs, version manifest, data schema, full metrics, additional baselines, audit procedure.

### 20.2 Claims-and-evidence ledger

Maintain `research/claims_evidence.csv` with:

- paper claim;
- exact result table/figure;
- raw result file;
- experiment ID/config hash;
- data split IDs;
- CI/denominator;
- assumptions;
- closest paper contrast;
- approved phrasing.

Every quantitative or comparative statement in the manuscript must map to this ledger. Claims without evidence must be removed or rewritten as hypotheses/limitations.

### 20.3 Reproducibility artifact

Include:

- installation instructions;
- exact Python/package/benchmark/model versions;
- code commit hash and lock file;
- data-acquisition/recreation instructions and licenses;
- split IDs or deterministic split-generation script;
- every configuration needed to reproduce main tables;
- scripts for metrics/figures;
- raw score files where legally distributable;
- compute/API-cost statement;
- known non-determinism and failed-run policy;
- all material deviations from the analysis plan.

### 20.4 Responsible publication claims

Never write, without evidence:

- “guarantees detection of hijacks”;
- “achieves 100% containment”;
- “generalizes to unseen attacks” based on one held-out template set;
- “real-world ready” based solely on benchmark tasks;
- “first method” based on an informal search;
- “zero overhead” without a measured workload and hardware context;
- “statistically significant improvement” without the corresponding test/CI and independent unit definitions.

---

## 21. Definition of done

The project is ready for a serious paper submission review only when all applicable boxes below are satisfied.

### Research
- [ ] Closest prior papers read in full and recorded in the literature matrix.
- [ ] Novelty matrix includes direct competitors and explicit overlap analysis.
- [ ] Primary RQ, hypotheses, and primary metric frozen before final test evaluation.
- [ ] Claims and limitations are proportionate to the evidence.

### Environment and benchmark
- [ ] Python virtual environment is isolated and dependencies are locked.
- [ ] Antigravity sandbox or another OS/container/VM boundary is configured where available.
- [ ] Benchmark code/task versions are pinned and recorded separately.
- [ ] No-defense smoke test reproduces and logs outcomes.
- [ ] No production credentials or real tool side effects are used.

### Data and correctness
- [ ] Trace schema validated.
- [ ] Pre-execution interface excludes future observations/outcomes.
- [ ] Outcome labels and checker semantics audited.
- [ ] Splits are task-disjoint and saved immutably.
- [ ] Calibration set is separate and sufficiently large for the selected alpha.
- [ ] Failed runs and exclusions are logged, not silently dropped.

### Models and evaluation
- [ ] Mandatory simple baselines implemented.
- [ ] Strongest feasible direct baseline attempted or omitted with documented justification.
- [ ] Proposed model runs and scores are reproducible.
- [ ] Conformal threshold math is unit tested.
- [ ] Primary and secondary metrics computed from raw results.
- [ ] Clustered uncertainty estimates and denominators reported.
- [ ] Held-out and shift/adaptive/in-loop evaluations completed or clearly scoped as limitations.
- [ ] Ablations support every core component claim.

### Paper/artifact
- [ ] Figures/tables regenerate from scripts.
- [ ] Claims-evidence ledger is complete.
- [ ] Data and code licenses are checked.
- [ ] README and clean-environment reproduction pass.
- [ ] Negative results and limitations are reported.
- [ ] Submission venue requirements/deadlines are independently checked.

---

## 22. Suggested prompts for Antigravity

Use these one at a time. Do not submit all phases as one mega-prompt.

### Prompt 0 — Inspect and plan only

```text
Read AGENTWATCH_DIRECTION_A_SPEC.md and the existing repository. Do not edit files or install dependencies yet. Summarize the project objective, current novelty risks, required phases, and repository state. Identify any contradictions or missing decisions. Propose the smallest implementation plan for Phase 0/1 only. Do not invent benchmark versions, paper results, or repository tags. Wait for review before making changes.
```

### Prompt 1 — Project skeleton and secure environment

```text
Implement only the repository skeleton and environment verification described in Sections 13–17 of AGENTWATCH_DIRECTION_A_SPEC.md. Create .gitignore first, keep raw data/runs/models out of Git, create pyproject.toml with minimal dependencies, and add AGENTS.md with the specification's safety and phase-gate rules. Do not download a large model or generate benchmark traces. Add a doctor command that prints versions/paths and checks for secrets without displaying secret values. Add unit tests. Run only reviewed commands and report exactly what changed, what passed, and what remains unresolved.
```

### Prompt 2 — Benchmark compatibility audit

```text
Implement only a thin AgentDojo version check and adapter skeleton. First inspect the official AgentDojo docs/repository and confirm the actual package version, code commit, task revision, Python requirements, license, and supported model adapters. Do not assume task revision and package version are identical. Run the official minimal quickstart only after approval. Capture command/output/version metadata and create docs/benchmark_setup.md. Do not implement the learned monitor yet.
```

### Prompt 3 — Trace schema and leakage tests

```text
Implement canonical trace schemas, JSONL read/write, validation, and a PreExecutionEvent type containing only the trusted goal, prior completed steps, current proposed action, and permitted metadata. Implement tests proving current/future observations, final labels, security_success, and t_harm cannot enter inference features. Add synthetic fixtures only. Do not generate real benchmark runs until the tests pass.
```

### Prompt 4 — Pilot and label audit

```text
Implement a minimal smoke-test runner for one benign and one attack-configured AgentDojo case, using only simulated tools. Verify whether the injection was actually exposed, whether the environment security checker indicates attacker-goal success, and whether utility completion is recorded. Store an immutable run manifest and JSONL trace. Stop if labels or decision timing are ambiguous. Do not claim the pilot proves any model performance.
```

### Prompt 5 — Baselines only

```text
Implement the mandatory baseline suite in Section 11 of AGENTWATCH_DIRECTION_A_SPEC.md, one at a time, on the frozen pilot split. Save raw per-prefix scores, config hashes, versions, and results. Do not implement the proposed goal-conditioned monitor until the baselines, split integrity, and metrics are validated. Do not call a proxy implementation by the original paper's method name.
```

### Prompt 6 — Proposed monitor

```text
Implement the minimal causal GRU goal-conditioned monitor defined in Section 8 only after the baseline gate has passed. Enforce prefix-only inference structurally. Keep thought text disabled in the main configuration. Add a goal-conditioning ablation and tests for deterministic feature extraction. Train only on training data, choose hyperparameters only on validation data, and leave calibration and final test data untouched.
```

### Prompt 7 — Calibration and evaluation

```text
Implement the split-conformal maximum-score threshold and metric definitions exactly as written in Sections 9 and 12. Include tests for the order statistic, insufficient calibration size, per-trajectory FPR, and flags after t_harm. Calibration data may set the threshold but must not be used for model selection. Save the threshold, calibration IDs, alpha, sample count, and score definition. Run only on approved frozen splits.
```

### Prompt 8 — Final audit

```text
Do not modify the model or rerun experiments automatically. Audit the frozen run manifests, data splits, label counts, test leakage checks, confidence intervals, figure-generation scripts, citations, and claims-evidence ledger. List discrepancies and unsupported claims. Regenerate tables from raw result files only after approval. Do not invent missing outputs or replace failures with successful values.
```

---

## 23. Reference links and citation checklist

### Benchmarks and official implementations

- AgentDojo paper: https://arxiv.org/abs/2406.13352
- AgentDojo documentation: https://agentdojo.spylab.ai/
- AgentDojo official GitHub: https://github.com/ethz-spylab/agentdojo
- AgentDojo PyPI: https://pypi.org/project/agentdojo/
- AgentDyn paper: https://arxiv.org/abs/2602.03117
- AgentDyn official GitHub: https://github.com/SaFo-Lab/AgentDyn
- AutoDojo paper: https://arxiv.org/abs/2606.15057
- AutoDojo code: https://github.com/xhOwenMa/AutoDojo
- LlamaFirewall: https://github.com/meta-llama/PurpleLlama/tree/main/LlamaFirewall

### Closest research papers

- Trajectory Guard: https://arxiv.org/abs/2601.00516
- DriftNet: https://arxiv.org/abs/2609.10892
- AgentDrift: https://arxiv.org/abs/2609.06972
- TraceAegis: https://arxiv.org/abs/2510.11203
- TrajAD: https://arxiv.org/abs/2602.06443
- AgentSentry: https://arxiv.org/abs/2602.22724
- Agent-as-a-Proxy: https://arxiv.org/abs/2602.05066
- Hidden-state probes: https://arxiv.org/abs/2608.02657
- LlamaFirewall paper: https://arxiv.org/abs/2505.03574
- MELON (ICML 2025, PMLR): https://proceedings.mlr.press/v267/zhu25z.html ; arXiv version: https://arxiv.org/abs/2502.05174 ; code: https://github.com/kaijiezhu11/MELON
- Firewall-focused evaluation: https://arxiv.org/abs/2510.05244
- ProbGuard/Pro2Guard: https://arxiv.org/abs/2508.00500

### Environment and coding-agent safety

- Google Antigravity sandbox documentation: https://antigravity.google/docs/sandbox/
- Google Antigravity settings: https://antigravity.google/docs/settings?tab=ide
- Google Antigravity agent settings: https://www.antigravity.google/docs/agent-settings
- Python virtual environments: https://docs.python.org/3/library/venv.html
- Python `venv` tutorial: https://docs.python.org/3/tutorial/venv.html
- Docker security overview: https://docs.docker.com/engine/security/

**Citation procedure:** open and read the full papers before drafting related work. Verify titles, authors, publication status, versions, repository ownership, commit/tag, license, and exact claims. A link in this file is a starting point, not a substitute for full-paper review. Recheck all links and conference requirements immediately before submission.

---

## Appendix A — Canonical trace schema

This is an illustrative schema, not a completed benchmark record. Refine only with a documented reason and preserve schema versioning.

```json
{
  "schema_version": "1.0",
  "run_id": "unique-run-id",
  "pair_id": "optional-paired-condition-id",
  "benchmark": "agentdojo",
  "benchmark_package_version": "exact-version-or-null",
  "benchmark_commit": "exact-commit-or-null",
  "task_revision": "exact-task-revision-or-null",
  "suite": "workspace",
  "user_task_id": "task-id",
  "injection_task_id": null,
  "attack_template_family": null,
  "attack_level": "L0",
  "agent_provider": "provider-name",
  "agent_model_version": "exact-model-version",
  "seed": 17,
  "goal": "synthetic user goal",
  "injection_configured": false,
  "injection_visible": false,
  "trajectory_label": "BENIGN",
  "security_success": false,
  "utility_success": true,
  "agent_finished": true,
  "t_harm": null,
  "steps": [
    {
      "step_index": 1,
      "prior_history_ref": "prefix-1-or-inline-history",
      "proposed_action": {
        "tool": "search_messages",
        "args": {"query": "synthetic query"}
      },
      "untrusted_sources_in_prefix": [],
      "provenance_features": {},
      "monitor_score": null,
      "threshold": null,
      "monitor_decision": "ALLOW",
      "decision_timestamp_ms": null,
      "tool_executed": true,
      "observation_after_execution": "synthetic observation",
      "injection_visible_after_execution": false,
      "tool_latency_ms": null
    }
  ],
  "code_commit": "git-sha",
  "config_hash": "sha256-or-null",
  "completed_at_utc": "ISO-8601 timestamp",
  "failure_status": null
}
```

Schema rules:

1. A scorer receives only the fields available before the call executes. `observation_after_execution`, `security_success`, `utility_success`, `trajectory_label`, and `t_harm` are evaluation/logging fields, not inference features.
2. The stored complete trace may include the completed observation after the decision, but the pre-execution event object must not.
3. If the benchmark does not expose a field, store `null` plus a reason rather than fabricating a value.
4. Preserve raw benchmark outcome fields alongside the normalized label.
5. Version the schema when fields or semantics change and write a migration script rather than silently rewriting older traces.

---

## Appendix B — Experimental result table templates

### B.1 Detection metrics

| Method | Train supervision | Test traces | TPR_pre @ 5% FPR target | Empirical FPR_traj (95% CI) | AUROC | AUPRC (prevalence) | Median lead time | Unique tasks | Notes |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| B1 transition | Benign only | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| B2 embedding anomaly | Benign only | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| B3 content detector | Public detector | TBD | TBD | TBD | TBD | TBD | N/A | TBD | TBD |
| B4 unconditioned sequence | Benign only | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| B5 Trajectory Guard | Paper-defined | TBD | TBD | TBD | TBD | TBD | TBD | TBD | Reproduction/proxy label |
| Proposed goal-conditioned | Benign only | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| Supervised oracle | Supervised | TBD | TBD | TBD | TBD | TBD | TBD | TBD | Upper-bound reference |

### B.2 End-to-end intervention

| Defense | Attack condition | ASR after intervention | Benign task success | Benign interruption rate | Additional latency | Cost/run | Unique tasks/runs | Notes |
|---|---|---:|---:|---:|---:|---:|---:|---|
| None | L0 | TBD | TBD | 0 by definition | TBD | TBD | TBD | Baseline |
| Proposed monitor | L0 | TBD | TBD | TBD | TBD | TBD | TBD | Frozen threshold |
| Proposed monitor | L1/L2 | TBD | TBD | TBD | TBD | TBD | TBD | Budget stated |
| Strongest baseline | L0 | TBD | TBD | TBD | TBD | TBD | TBD | Version/policy stated |

Never put invented values in these tables. `TBD` means an experiment has not yet been run or audited.

---

## Appendix C — Researcher's running checklist

### Before coding

- [ ] Read the full closest papers, including supplementary material.
- [ ] Verify current implementation repositories and licenses.
- [ ] Fill the novelty matrix and identify the exact gap.
- [ ] Freeze the threat model and pre-execution definition.
- [ ] Create a Git repository and `.gitignore`.
- [ ] Create `.venv` and configure OS/container isolation.
- [ ] Keep API keys out of Git and traces.

### Before generating the corpus

- [ ] Pin AgentDojo code and task revision separately.
- [ ] Run official smoke tests.
- [ ] Confirm how security and utility success are calculated.
- [ ] Test that exposure is measured separately from attack configuration.
- [ ] Validate trace schema and no-future-leakage tests.
- [ ] Estimate API/compute cost and independent task count.

### Before training

- [ ] Audit labels.
- [ ] Freeze train/validation/calibration/test task IDs.
- [ ] Check attack-template and agent splits.
- [ ] Save the analysis plan.
- [ ] Implement simple baselines first.
- [ ] Confirm no final-test access in training/selection scripts.

### Before final evaluation

- [ ] Freeze features, model, preprocessing, threshold protocol, and configs.
- [ ] Save calibration IDs and threshold artifacts.
- [ ] Confirm calibration sample size supports the selected alpha.
- [ ] Check every inference feature against the threat boundary.
- [ ] Confirm baseline versions and same-test comparisons.
- [ ] Use the frozen evaluation plan and log every failed run.

### Before writing/submission

- [ ] Report all primary results, including negative findings.
- [ ] Include denominators, independent tasks, confidence intervals, and seeds.
- [ ] Report FPR per trajectory, not only per step.
- [ ] Separate offline detection from in-loop attack reduction.
- [ ] Verify every paper claim against the claims-evidence ledger.
- [ ] Review novelty and citations once more.
- [ ] Check data/model licenses and venue requirements.
- [ ] Reproduce tables and plots from a clean checkout.

---

**End of specification.**
