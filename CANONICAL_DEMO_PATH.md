# Canonical Demo Path

This document defines the primary demonstration sequence for Hexarch Guardrails. It exists to keep external messaging consistent and prevent narrative fragmentation. Each demo proves one enforcement dimension; their ordering prioritizes immediacy of engineering value and reproducibility.

## Ordered Demo List

### 1. Threshold Pre-Execution Blocking
- **What it proves**: Request-count gating before side effects.
- **Axis**: Pre-execution control, execution stability.
- **Strategic value**: Simplest reproducible pattern; high immediate recognition for anyone who has debugged runaway loops.
- **Audience fit**: Practitioners building automation workflows; platform teams evaluating control planes.
- **Demo location**: `n8n/ADDING_PRE_EXECUTION_POLICY_ENFORCEMENT_TO_N8N_IN_15_MINUTES.md` + `node-red/ADDING_PRE_EXECUTION_POLICY_ENFORCEMENT_TO_NODE_RED_IN_15_MINUTES.md`

### 2. Recursion / Loop Prevention
- **What it proves**: Depth-based gating for self-triggering flows.
- **Axis**: Execution stability, structural safety.
- **Strategic value**: Demonstrates policy enforcement on iterative/recursive call patterns; addresses amplification beyond simple retry loops.
- **Audience fit**: Workflow builders using node-based orchestrators; AI agent developers.
- **Demo location**: `examples/public-demos/RECURSION_LOOP_PREVENTION_NODE_RED.md`

### 3. Model Usage Containment
- **What it proves**: Combined allowlist + ceiling enforcement before LLM invocation.
- **Axis**: Model containment, cost governance, AI-specific policy.
- **Strategic value**: Extends pattern into AI-specific domain; shows multi-rule policy composition.
- **Audience fit**: Teams building AI agents; platform teams enforcing organizational model usage constraints.
- **Demo location**: `examples/public-demos/MODEL_USAGE_CONTAINMENT.md`

## Recommendation for External First Exposure

**Lead with threshold demo.**
- Reason: Shortest path to concrete allow/deny routing with universally understood failure mode (runaway request count).
- Format: Link directly to n8n or Node-RED guide depending on target community.
- Follow-up: Recursion demo (if audience is workflow-native) or model containment (if audience is AI-native).

**Do not distribute all three simultaneously in initial outreach.**
- Rationale: Sequential exposure allows refinement of messaging and validation of demo clarity before expanding surface area.
