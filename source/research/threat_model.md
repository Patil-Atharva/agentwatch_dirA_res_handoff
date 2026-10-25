# AgentWatch-A: Threat Model and Assumptions

Adheres to Section 5 of AGENTWATCH_DIRECTION_A_SPEC.md.

## 1. System Model
- An autonomous tool-using agent pursues a trusted user goal `g`.
- The agent proposes actions `a_t` based on prior context and observations.
- Untrusted tool outputs (webpages, emails, search results) may contain prompt injection payloads.
- A trusted pre-execution interceptor observes the proposed tool call `a_t` before execution.

## 2. Attacker Capabilities
- Can inject arbitrary text into untrusted content read by the agent.
- Can use benchmark injection templates, obfuscation, or adaptive modifications.
- Cannot modify the trusted goal, system prompt, tool interceptor, or monitor weights.
- Cannot observe future steps or access the host process.

## 3. Pre-Execution Boundary (Strict Invariant)
At decision step `t`, the monitor inspects:
- Trusted user goal `g`.
- Prior completed steps `(a_1, o_1), ..., (a_{t-1}, o_{t-1})`.
- The proposed action `a_t` and arguments.
- Provenance/trust metadata of prior observations.

The monitor MUST NOT inspect:
- The execution result of `a_t` (`o_t`).
- Any future action `a_{t+k}` or observation `o_{t+k}`.
- Ground-truth task outcome labels or `t_harm`.
