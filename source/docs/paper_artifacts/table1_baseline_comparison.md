# Table 1: Baseline Comparison and Feature Separation

Direct mapping to `data/result_registry.json`.

| Model / Baseline | Benign ($\mu$) | Resisted ($\mu$) | Hijacked ($\mu$) | Separation ($\Delta$) | Analysis |
|---|---|---|---|---|---|
| **B1 (Transition Bigram)** | 0.2000 | 0.0000 | 1.0000 | +0.8000 | High separation on single-step transitions; fails on multi-step variations. |
| **B2 (Isolation Forest)** | 0.5324 | 0.3477 | 0.5859 | +0.0535 | Flattening history destroys temporal sequence order. |
| **B2 (One-Class SVM)** | 0.0000 | 1.0000 | 1.0000 | +1.0000* | Catastrophic false alarms on resisted workflows ($1.0000$). |
| **B3 (Content Detector)** | 0.0000 | 1.0000 | 1.0000 | +1.0000* | Lacks goal awareness; flags whenever injection text appears in observation. |
| **B4 (Unconditioned Sequence)** | 0.2000 | 0.0000 | 0.3846 | +0.1846 | Limited sequence discriminability without goal conditioning. |
| **GoalConditionedGRU (Ablated)** | 0.4934 | 0.4903 | 0.8500 | +0.3566 | Without goal $g$, benign false alarm baseline rises. |
| **GoalConditionedGRU (Full)** | **0.5418** | **0.5217** | **0.8500** | **+0.3082** | Goal conditioning lowers benign risk and resisted risk, maximizing separation. |
| **B6 (Supervised Oracle)** | 0.0064 | 0.0064 | 0.9613 | +0.9549 | Supervised upper bound trained on post-harm ground truth labels. |

*\*Flagged legitimately resisted executions as attacks.*
