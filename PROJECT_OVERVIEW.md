# AgentWatch-A: Project Overview & Scientific Architecture

**Project**: AgentWatch-A (Direction A Specification v1.0)  
**Authoritative Reference**: [`AGENTWATCH_DIRECTION_A_SPEC.md`](source/AGENTWATCH_DIRECTION_A_SPEC.md)  

---

## 1. Problem Statement & Motivation

Autonomous Large Language Model (LLM) agents equipped with external tools (e.g. email clients, file systems, calendar schedulers) are vulnerable to **Indirect Prompt Injection (IPI)**. When an agent processes untrusted external content containing malicious instructions, the underlying LLM may be hijacked into executing unauthorized actions (e.g., exfiltrating credentials or altering sensitive records).

Existing defenses suffer critical failure modes:
1. **Static Observation Scanning (e.g., LlamaFirewall)**: Scans observation strings for prompt injection tokens. However, legitimate benign workflows often process untrusted content quoting injection strings (e.g., summarizing support emails). Observation scanners trigger severe false alarms on such tasks.
2. **Post-Execution Auditing (e.g., DriftNet, TraceAegis)**: Examines full traces offline after episode completion. While useful forensically, detection occurs *after* irreversible harm (data deletion, financial transfer, exfiltration) has already transpired.
3. **Heavy LLM Guardrails (e.g., AgentSentry)**: Employs a secondary LLM to judge every action context. This introduces 300–800ms of latency and substantial API token costs.

**AgentWatch-A** addresses these deficiencies by proposing an **online, black-box, pre-execution runtime monitor** that enforces the strict timing invariant:
\[
t_{\text{flag}} \le t_{\text{harm}}
\]
while controlling trajectory-level false positive rates ($FPR_{\text{traj}} \le \alpha$) using distribution-free split-conformal calibration on benign trajectory maxima.

---

## 2. Threat Model and Boundary Invariants

- **Attacker Capabilities**: The attacker cannot access user prompts, model weights, or system prompts. The attacker can only place malicious payloads into external data objects read by tools (calendar descriptions, email bodies, file contents).
- **Trusted Channel**: The user's initial prompt $g$ and the monitor execution code are trusted.
- **Untrusted Channel**: Environment observations $o_t$ containing third-party or untrusted text.
- **Mediation Point**: The monitor sits strictly at the **Tool Execution Boundary**. The proposed tool call $a_t = (\text{tool}, \text{args})$ is intercepted before the environment runtime executes the tool implementation.
- **Out of Scope**: Direct jailbreaks by the primary user, network MITM, and multi-agent coordination (Direction B).

---

## 3. Implemented Technical Architecture

The AgentWatch-A architecture comprises four tightly integrated modules:

```
[User Goal g]
      │
      ▼
┌───────────────┐     Proposed Call at      ┌─────────────────────────┐
│ Tool-Using    │ ────────────────────────> │ PreExecutionInterceptor │
│ LLM Agent     │ <──────────────────────── │ (AgentWatch-A Monitor)  │
└───────────────┘        ALLOW / BLOCK      └───────────┬─────────────┘
                                                        │
                      ┌─────────────────────────────────┴───────────────────┐
                      │ 1. Deterministic CRC32 Hash Encoding (Frozen Text)   │
                      │ 2. 7-Dimensional Argument Provenance Vector p(a_t)  │
                      │ 3. Causal Goal-Conditioned Recurrent GRU State h_t  │
                      │ 4. Cosine Metric Projection to Shared Latent Space  │
                      │ 5. Conformal Max-Score Threshold Calibration tau_hat│
                      └─────────────────────────────────────────────────────┘
```

1. **Deterministic Feature Encoding**: Words are hashed into fixed vocabulary buckets via `zlib.crc32(word.encode()) % 10000`, guaranteeing 100% bit-exact determinism across independent Python processes without cloud API dependencies.
2. **7D Argument Provenance Extraction**: Deterministically extracts argument length, hex density, base64 markers, domain mismatches, control syntax, and an untrusted taint overlap flag $p_{\text{taint}} \in \{0, 1\}$.
3. **Causal Goal-Conditioned GRU**: Hidden state $h_t = \text{GRU}(x_t, h_{t-1})$ processes historical causal prefixes. The trajectory state $h_t$ and goal embedding $e_g$ are projected into a shared 32D metric space via normalized linear projections. Anomaly score:
   \[
   s_t = \sigma\left(\gamma (1 - \langle z_g, z_t \rangle) + \beta \cdot p_{\text{taint}}(a_t) \cdot p_{\text{impact}}(a_t)\right)
   \]
4. **Split-Conformal Calibration on Trajectory Maxima**:
   \[
   S_j = \max_{1 \le t \le |T_j|} s_t(T_j), \quad \hat{\tau} = S_{(k)}, \quad k = \lceil(n+1)(1-\alpha)\rceil
   \]
   Guarantees marginal trajectory false alarm coverage under exchangeability.
