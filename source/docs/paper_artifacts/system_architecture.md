# AgentWatch-A: System Architecture Diagrams

Adheres to Section 6.1, Section 8, and Section 10.5 of [`AGENTWATCH_DIRECTION_A_SPEC.md`](file:///C:/Users/Ayush/Documents/GitHub/research%20project/revised_agentwatch__dir_a/AGENTWATCH_DIRECTION_A_SPEC.md).

---

## 1. Pre-Execution Interception Boundary

```
User Query / Goal (g)
         │
         ▼
┌─────────────────┐       Proposed Action: a_t = (tool, args)
│    LLM Agent    │──────────────────────────────────────┐
└─────────────────┘                                      │
         ▲                                               ▼
         │                                   ┌───────────────────────┐
         │                                   │ PreExecutionInterceptor│
         │                                   └───────────────────────┘
         │                                               │
         │                                               ▼
         │                                  ┌─────────────────────────┐
         │                                  │  AgentWatch-A Monitor   │
         │                                  │   (Goal-Conditioned)    │
         │                                  └─────────────────────────┘
         │                                               │
         │                                      Risk Score: R_t in [0, 1]
         │                                               │
         │                                               ▼
         │                                   ┌───────────────────────┐
         │                                   │    Decision Policy    │
         │                                   │ (Threshold \hat{\tau})│
         │                                   └───────────────────────┘
         │                                          │         │
         │                        ALLOW (R_t <= \tau)│         │ BLOCK (R_t > \tau)
         │                                          ▼         ▼
         │                                   ┌─────────┐   ┌─────────┐
         │                                   │ Tool    │   │ Early   │
         │                                   │ Executor│   │ Return  │
         │                                   └─────────┘   └─────────┘
         │                                          │      (Tool NOT
         │                               Observation│       executed)
         │                                   o_t    ▼
         └──────────────────────────────────────────┘
```

---

## 2. Causal Goal-Conditioned Sequence Architecture

```
User Goal: g ─────────► [ Deterministic Text Encoder ] ─────────► e(g) ───► h_0 = tanh(W_g e(g))
                                                                              │
                                                                              ▼
Step 0: (a_0, o_0) ───► [ Feature & Provenance Encoder ] ──────────────► [ GRU Cell ] ───► h_1
                                                                              │
                                                                              ▼
Step 1: (a_1, o_1) ───► [ Feature & Provenance Encoder ] ──────────────► [ GRU Cell ] ───► h_2
                                                                              │
                                                                              ▼
Proposed: a_t ────────► [ Feature & Provenance Encoder ] ──────────────► [ GRU Cell ] ───► h_t
                                                                              │
                                 ┌────────────────────────────────────────────┴────────┐
                                 ▼                                                     ▼
                  [ Cosine Similarity with Goal ]                        [ Multilayer Perceptron ]
                        cos(W_proj h_t, e(g))                             Provenance & Taint Risk
                                 │                                                     │
                                 └───────────────────────┬─────────────────────────────┘
                                                         ▼
                                            Risk Score R_t in [0.0, 1.0]
```

---

## 3. Two-Track Evaluation Model (Section 10.5)

```
                       ┌─────────────────────────┐
                       │ Canonical Traces (JSONL)│
                       └─────────────────────────┘
                                    │
           ┌────────────────────────┴────────────────────────┐
           ▼                                                 ▼
┌───────────────────────────┐                     ┌───────────────────────────┐
│ Track 1: Offline Replay   │                     │ Track 2: In-Loop Interv.  │
│ - Feeds prefix events     │                     │ - Live agent execution    │
│ - Trajectory unchanged    │                     │ - Halts malicious tools   │
│ - Evaluates:              │                     │ - Evaluates:              │
│   * TPR_pre               │                     │   * In-loop ASR reduction │
│   * FPR_benign            │                     │   * Benign utility        │
│   * AUROC / AUPRC         │                     │   * False Interruption    │
│   * Lead time (steps)     │                     │   * Inference Latency     │
└───────────────────────────┘                     └───────────────────────────┘
```
