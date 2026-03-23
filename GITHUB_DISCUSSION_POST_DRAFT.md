# GitHub Discussion Draft: Pre-Execution Policy Enforcement for Automation Systems

## Title
Pre-Execution Policy Enforcement for Automation Systems

## Body

### Problem
Automation platforms like n8n and Node-RED execute API calls, run parallel branches, and invoke LLMs without structural enforcement of cost, recursion, or model usage boundaries. Runtime alerts and post-execution billing thresholds report violations after side effects have propagated through downstream systems. Testing gives local confidence; production gives surprises.

### Pattern
A pre-execution policy gate checks authorization before continuation. The orchestrator sends resource, action, and context (request count, recursion depth, model, token count) to an external `/authorize` endpoint. A structured policy decision (allow/deny + reason) controls whether the flow proceeds or halts.

This is deterministic: identical context yields identical decisions. The orchestrator sees deny reasons before invoking external APIs. No retry guessing. No partial execution.

### Demonstration
We built a threshold enforcement demo for Node-RED:

- **Flow**: [Importable JSON](node-red/flows/hexarch-pre-execution-threshold-guard.json)
- **Guide**: [15-minute walkthrough](node-red/ADDING_PRE_EXECUTION_POLICY_ENFORCEMENT_TO_NODE_RED_IN_15_MINUTES.md)
- **Behavior**: At `request_count=7`, `/authorize` returns `{"allowed": false, "decision": "DENY", "reason": "policy_denied:bc57117f..."}`. The switch node routes to a blocked output. No downstream API is called.

The same pattern extends to recursion depth gating and model allowlist plus token ceiling enforcement. Rule JSON shapes are [here](examples/public-demos/).

### Engineering Question
Where does pre-execution policy add the most clarity in your automation stack? What context fields would you check before invoking provider APIs, spawning loops, or calling unbounded branches?

If you've built analogous gating patterns, what failure modes have you observed when authorization happens after execution?

---

**Related**: [CANONICAL_DEMO_PATH.md](CANONICAL_DEMO_PATH.md) | [HEXARCH_POSITIONING_AXES.md](HEXARCH_POSITIONING_AXES.md)
