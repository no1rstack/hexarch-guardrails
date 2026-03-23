# Technical Guarantees

Hexarch Guardrails provides pre-execution policy enforcement for automation systems, agent workflows, and LLM orchestration. This document defines what the system guarantees and what it does not.

## Enforceable Guarantees

- **Deterministic allow/deny decisions**: Identical input context, resource, and action produce identical authorization results under the same rule set. No probabilistic evaluation. No model-based classification.

- **Pre-execution evaluation**: The `/authorize` endpoint returns a decision before the caller invokes downstream APIs, triggers branches, or initiates side effects. Deny decisions include structured reason strings with policy identifiers.

- **Policy isolation by scope**: Rules bind to policies with explicit scope (GLOBAL, ORGANIZATION, TEAM, USER, RESOURCE). Evaluation filters policies by requested scope before rule execution. Scope leakage is structurally prevented.

- **Structured response output**: Every `/authorize` response contains `allowed` (boolean), `decision` (ALLOW/DENY), `reason` (nullable string), and `policies` (array of policy metadata). No ambiguous states. No silent failures.

- **Rule condition evaluation**: The rule engine evaluates JSON condition objects with operators (`lte`, `gte`, `in`, `equals`, `gt`, `lt`) against context paths (e.g., `input.context.request_count`). Field resolution errors result in condition failure, not exception propagation.

- **Failure mode explicitness**: Policies declare `failure_mode` (FAIL_CLOSED or FAIL_OPEN). When rule evaluation encounters resolution errors or missing context fields, the policy's failure mode determines the authorization outcome. This behavior is documented per-policy.

## Explicit Non-Guarantees

- **Not a runtime sandbox**: Hexarch does not execute user code, intercept system calls, or constrain process boundaries. It evaluates policies and returns decisions. The caller enforces the decision by choosing whether to proceed with downstream actions.

- **Not a logic correctness validator**: Hexarch does not analyze workflow graphs for infinite loops, race conditions, or semantic errors. It evaluates context against rules. If the caller provides incorrect context or misinterprets deny reasons, Hexarch cannot detect those errors.

- **Not a replacement for IAM**: Hexarch does not authenticate users, manage credentials, or enforce network access control. It assumes the caller has already authenticated and provides identity context as part of the authorization request. Hexarch evaluates policy; identity verification is upstream.

- **Not a performance accelerator**: Policy evaluation adds latency to the request path. For batch workflows invoking thousands of operations, pre-execution checks impose overhead proportional to request volume. Hexarch prioritizes correctness and determinism over sub-millisecond response times.

- **Not a universal policy language**: The rule condition DSL supports common operators and context path resolution. Complex predicates (regex matching, time-based windows, statistical aggregation) require preprocessing in the caller or custom rule extensions. The DSL is intentionally minimal.

## Failure Mode Behavior

### Policy engine unavailable

When the `/authorize` endpoint is unreachable (network partition, service restart, configuration error), the orchestrator must decide how to proceed:

- **Deny-by-default**: Treat unreachable policy engine as DENY. Halt workflow execution. Log failure reason. This matches FAIL_CLOSED semantics.

- **Allow-with-warning**: Proceed with downstream action but emit a warning signal for audit/alerting. This matches FAIL_OPEN semantics with observability.

Hexarch cannot enforce this decision at the orchestrator level. The integration layer (n8n flow, Node-RED switch node, application middleware) controls fallback behavior.

### Rule evaluation error

When a rule condition references a context field that does not exist (`input.context.missing_field`), the rule engine does not throw an exception. Instead:

- The condition evaluates to `false`.
- The policy's `failure_mode` determines the final decision.
- If FAIL_CLOSED: The policy contributes a DENY signal.
- If FAIL_OPEN: The policy contributes an ALLOW signal.

This prevents silent partial evaluation. Every rule participates in the decision with explicit failure semantics.

### Malformed authorization request

If the `/authorize` request omits required fields (`action`, `resource`) or provides invalid JSON, the API returns HTTP 422 with structured validation errors. No authorization decision is made. The caller receives a clear signal that the request cannot be evaluated.

This is not a policy decision. It is a contract violation.
