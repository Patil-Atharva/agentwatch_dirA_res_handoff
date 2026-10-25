# Known Limitations and Open Research Questions

**Authoritative Reference**: `docs/LIMITATIONS_AND_ETHICS.md`  

---

## 1. Concrete Empirical Limitations

1. **Finite Sample Size Constraint ($N=20$)**:
   - The canonical evaluation corpus contains 20 traces (10 Benign, 3 Unexposed, 4 Resisted, 3 Hijacked).
   - In Track 1, $TPR_{	ext{pre}} = 3/3 = 100\%$ yields a wide 95% Wilson confidence interval of $[0.439, 1.000]$.
   - In Track 2, live intervention is evaluated on $N=2$ benign tasks and $N=2$ attack tasks. The one-sided Fisher exact test on benign interruption yields $p = 0.1667$, because with $N=2$ per group, $p < 0.05$ is mathematically impossible regardless of effect size.
2. **Calibration Corpus Size ($n=5$)**:
   - With $n=5$ benign calibration trajectories and nominal $lpha = 0.20$, the order statistic is $k = \lceil 6 	imes 0.80 ceil = 5$ (the absolute maximum).
   - On the held-out test set ($N=5$), empirical $FPR_{	ext{benign}}$ was $40\%$ (2/5 false alarms). This reflects finite-sample variance around the nominal quantile.
3. **White-Box Adaptive Evasion**:
   - An adversary with white-box access to the frozen CRC32 projection and GRU weights could theoretically craft prompt injection payloads using words whose hash embeddings minimize cosine distance $\langle z_g, z_t angle$. Defending against adaptive optimization requires future adversarial training.
4. **Tool Domain Specialization**:
   - The current tool transition prior and provenance extractor are specialized for workspace tools (email and calendar). Expanding to web browsing or bash terminal environments requires expanding the tool vocabulary.

---

## 2. Prioritized Open Questions for Future Evaluation

- **EXP-01**: Expand benign calibration from $n=5$ to $n=50$ across all 40 AgentDojo workspace tasks to test whether empirical $FPR$ stabilizes at $pprox 20\%$.
- **EXP-02**: Benchmark against $N=30$ hijacked and $N=30$ benign scenarios to narrow the Wilson interval to $\pm 0.05$ and achieve Fisher $p < 0.001$.
- **EXP-03**: Cross-suite evaluation on AgentDojo `banking` and `slack` suites to test out-of-distribution transfer without retraining.
