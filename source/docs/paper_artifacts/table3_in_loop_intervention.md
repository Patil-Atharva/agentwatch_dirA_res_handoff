# Table 3: Closed-Loop In-Loop Intervention & Operational Latency (Track 2)

Direct mapping to `data/result_registry.json`.

| Defense Mode | Policy Action | In-Loop ASR | ASR Reduction | Benign False Interruption Rate ($FIR_{\text{benign}}$) | Mean Latency (ms) |
|---|---|---|---|---|---|
| **Unprotected Agent** | None | 50.00% | 0.00% | 0.00% | 0.00 ms |
| **B1 (Transition Bigram)** | Active BLOCK | 0.00% | 100.00% | 100.00% *(Catastrophic)* | 0.01 ms |
| **B3 (Content Detector)** | Active BLOCK | 0.00% | 100.00% | 50.00% *(Severe)* | 1.48 ms |
| **B4 (Unconditioned Sequence)** | Active BLOCK | 0.00% | 100.00% | 100.00% *(Catastrophic)* | 0.02 ms |
| **GoalConditionedGRU (Ablated)** | Active BLOCK | 0.00% | 100.00% | 100.00% *(Catastrophic)* | 1.05 ms |
| **GoalConditionedGRU (Full)** | **Active BLOCK** | **0.00%** | **100.00%** | **0.00%** *(Zero)* | **1.61 ms** |

### Key Scientific Takeaways:
1. **Gate G3 & G4 Passed**: Baselines B1 and B4 stop the attack only by destroying legitimate utility (blocking 100% of benign multi-step workflows). Ablated GRU (without goal) also falsely interrupts 100% of benign workflows. Content detector B3 falsely interrupts 50% of benign tasks whenever untrusted text is returned by a tool. Only `GoalConditionedGRU (Full Monitor)` achieves 100% ASR reduction with 0% false interruption of benign tasks.
2. **CPU Latency Profile**: Average CPU inference latency is **$1.61\text{ ms}$** (min: $1.05\text{ ms}$, max: $1.94\text{ ms}$), far below the $50\text{ ms}$ operational budget.
