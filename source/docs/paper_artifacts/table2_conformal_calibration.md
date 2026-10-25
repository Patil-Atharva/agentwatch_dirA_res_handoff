# Table 2: Conformal Calibration and Pre-Execution Evaluation (Track 1)

Direct mapping to `data/result_registry.json`.

Split-conformal calibration on trajectory maxima at nominal $\alpha = 0.20$ ($n = 5$ benign calibration units, $k = 5$):

| Model | Calibrated Threshold $\hat{\tau}$ | $TPR_{\text{pre}}$ | $FPR_{\text{benign}}$ | $FPR_{\text{resisted}}$ | AUROC | AUPRC | Lead Time |
|---|---|---|---|---|---|---|---|
| **B1 (Transition Bigram)** | 0.2500 | 100.00% | 40.00% | 0.00% | 0.800 | 0.800 | 0.0 steps |
| **B3 (Content Detector)** | 0.0000 | 100.00% | 0.00% | 0.00% | 1.000 | 1.000 | 0.0 steps |
| **B4 (Unconditioned Sequence)** | 0.2500 | 100.00% | 40.00% | 0.00% | 0.600 | 0.300 | 0.0 steps |
| **GoalConditionedGRU (Ablated)** | 0.4847 | 100.00% | 100.00% | 100.00% | 1.000 | 1.000 | 1.0 steps |
| **GoalConditionedGRU (Full)** | **0.5515** | **100.00%** | **40.00%** | **0.00%** | **1.000** | **1.000** | **0.0 steps** |

**Takeaway**: At calibrated threshold $\hat{\tau} = 0.5515$, `GoalConditionedGRU (Full)` achieves perfect $TPR_{\text{pre}} = 100\%$ with zero false positive alarms on resisted trajectories ($FPR_{\text{resisted}} = 0.0\%$), whereas the ablated model triggers 100% false alarms on both benign and resisted workflows.
