# Hexarch System Overview

## What It Is

Hexarch Guardrails is a pre-execution policy enforcement engine for automation systems, agent workflows, and LLM orchestration. Before invoking external APIs, spawning branches, or calling language models, orchestrators send resource, action, and context to the `/authorize` endpoint. Hexarch evaluates structured policy rules and returns a deterministic allow/deny decision with reason strings. The orchestrator uses this decision to route execution: proceed on ALLOW, halt on DENY. This prevents runaway loops, cost overruns, unauthorized model usage, and recursion amplification before side effects propagate.

## What It Is Not

Hexarch is not a runtime sandbox, IAM system, or application logic validator. It does not execute user code, authenticate identities, or analyze workflow graphs for correctness. It evaluates context against rules and returns decisions. The orchestrator enforces those decisions by choosing whether to proceed with downstream actions. Hexarch does not intercept system calls, constrain network access, or block execution at the process level. Enforcement requires integration: the orchestrator must call `/authorize` before proceeding and must respect the decision.

## Architecture Summary

- **Policy Engine**: Evaluates JSON rule conditions against request context using operators (`lte`, `gte`, `in`, `equals`).
- **Scope Segmentation**: Policies bind to GLOBAL, ORGANIZATION, TEAM, USER, or RESOURCE scopes. Authorization requests filter policies by scope before evaluation.
- **Failure Modes**: Policies declare FAIL_CLOSED (deny on error) or FAIL_OPEN (allow on error). When rule conditions reference missing context fields, the policy's failure mode determines the outcome.
- **Deterministic Output**: Identical input context and rule set produce identical authorization decisions. No probabilistic evaluation, no model-based classification.
- **Pre-Execution Enforcement**: The `/authorize` endpoint completes before the orchestrator invokes downstream APIs. Deny decisions include structured reason strings with policy identifiers.

## Enforcement Lifecycle

```
┌──────────────┐
│   Workflow   │  Trigger event (schedule, webhook, manual)
│   Trigger    │
└──────┬───────┘
       │
       ▼
┌──────────────────────────────┐
│  Build /authorize Request    │  Construct: action, resource, context
│                              │  Example context: {request_count: 7, threshold: 5}
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│  POST /authorize (Hexarch)   │  Evaluate rules against context
│                              │  Filter policies by scope
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│  Receive Decision            │  {allowed: bool, decision: ALLOW/DENY, reason: string}
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│  Route Execution             │  If allowed: proceed to downstream API
│  (Switch / If Node)          │  If denied: halt workflow, log reason
└──────────────────────────────┘
```

## Document Structure

The system's operational characteristics are documented across focused files:

- **[TECHNICAL_GUARANTEES.md](TECHNICAL_GUARANTEES.md)**: Enforceable guarantees (determinism, pre-execution evaluation, policy isolation, structured responses) and explicit non-guarantees (not IAM, not sandbox, not logic validator). Includes failure mode behavior for network unavailability and rule evaluation errors.

- **[DETERMINISTIC_EVALUATION_EXAMPLE.md](DETERMINISTIC_EVALUATION_EXAMPLE.md)**: Concrete demonstration that identical input produces identical output, and modified rules produce different deterministic output. No commentary; pure inputs and responses.

- **[FAIL_CLOSED_BEHAVIOR.md](FAIL_CLOSED_BEHAVIOR.md)**: Operational handling of network failure (timeout, 503, connection refused) versus rule evaluation failure (missing context fields). Includes recommended integration patterns for deny-by-default and allow-with-warning.

- **[INTEGRATION_PATTERNS.md](INTEGRATION_PATTERNS.md)**: Four architectural insertion patterns (direct pre-execution gate, sidecar policy proxy, centralized policy service, multi-environment segmentation). Each with ASCII diagram, usage context, and tradeoff statement.

- **[POLICY_LIFECYCLE.md](POLICY_LIFECYCLE.md)**: Operational governance workflow from rule creation through deployment, audit retention, and deprecation. Includes versioning expectations, deployment topology, and audit log patterns.

- **[PERFORMANCE_ENVELOPE.md](PERFORMANCE_ENVELOPE.md)**: Evaluation complexity (O(P+R)), dominant latency source (network RTT), deployment topologies, and when not to use inline checks. Includes benchmarking command for measuring response times.

- **[HEXARCH_POSITIONING_AXES.md](HEXARCH_POSITIONING_AXES.md)**: Twelve governance dimensions that position Hexarch within the policy enforcement landscape. Used for internal alignment and message consistency.

- **[CANONICAL_DEMO_PATH.md](CANONICAL_DEMO_PATH.md)**: Ordered demo list (threshold → recursion → model containment) with strategic value and audience fit per demo. Defines primary entry point for external distribution.

## Integration Demonstrations

Three runnable demos with importable workflow artifacts:

1. **Threshold Pre-Execution Blocking** ([n8n](n8n/ADDING_PRE_EXECUTION_POLICY_ENFORCEMENT_TO_N8N_IN_15_MINUTES.md), [Node-RED](node-red/ADDING_PRE_EXECUTION_POLICY_ENFORCEMENT_TO_NODE_RED_IN_15_MINUTES.md)): Block execution when request count exceeds threshold. Demonstrates allow/deny routing with real HTTP responses.

2. **Recursion Loop Prevention** ([examples/public-demos/RECURSION_LOOP_PREVENTION_NODE_RED.md](examples/public-demos/RECURSION_LOOP_PREVENTION_NODE_RED.md)): Gate recursive invocations by depth. Shows ALLOW at depth=2, DENY at depth=4 with importable Node-RED flow.

3. **Model Usage Containment** ([examples/public-demos/MODEL_USAGE_CONTAINMENT.md](examples/public-demos/MODEL_USAGE_CONTAINMENT.md)): Enforce model allowlist plus token ceiling before LLM invocation. Includes three real response examples (allow, deny for disallowed model, deny for token overage).

All demos include real captured HTTP request/response traces from in-memory TestClient runs. No placeholders.

## Core Invariant

**Authorization decisions are rule-bound and pre-execution.** 

Given identical context, resource, action, and rule set, the `/authorize` endpoint returns identical decisions. Evaluation completes before the orchestrator proceeds with downstream operations. Deny decisions prevent execution; allow decisions gate continuation. The orchestrator controls enforcement by respecting the decision. Hexarch provides the decision; integration provides the enforcement.
