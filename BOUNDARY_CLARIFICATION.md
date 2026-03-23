# Boundary Clarification

This document defines what Hexarch Guardrails replaces and what it does not replace. Use this to determine whether Hexarch addresses a specific operational problem.

---

## What Hexarch Replaces

### Ad hoc threshold checks in workflow code
**Before**: Workflows contain inline conditionals checking request counts, token usage, or recursion depth scattered across flow definitions.  
**With Hexarch**: Centralized policy rules enforce thresholds via `/authorize` before execution. Threshold logic is versioned, auditable, and consistent across workflows.

### Inline model allowlists
**Before**: Model selection validated with hard-coded string comparisons in function nodes (`if model !== 'gpt-4' && model !== 'llama3' then error`).  
**With Hexarch**: Policy rules define model allowlists with JSON condition operators (`"op": "in", "value": ["gpt-4o-mini", "llama3"]`). Update centrally without modifying workflows.

### Hard-coded retry ceilings
**Before**: Retry logic embedded in catch blocks or loop nodes with magic-number limits (`max_retries = 5`).  
**With Hexarch**: Pre-execution policy checks retry count context before allowing continuation. Policy defines ceiling; workflow respects decision.

### Duplicate policy logic across workflows
**Before**: Each workflow reimplements the same threshold or allowlist checks. Drift occurs when one workflow updates logic and others do not.  
**With Hexarch**: Policy defined once, enforced consistently across all workflows calling `/authorize` with the same scope.

### Post-execution billing alerts
**Before**: Cost overruns detected after API invocation completes. Alerts fire, but charges have already accrued.  
**With Hexarch**: Pre-execution policy denies operations that exceed cost context thresholds. No downstream API call occurs on DENY.

### Manual policy enforcement audits
**Before**: Compliance verified by reviewing workflow code manually to confirm threshold checks exist and execute correctly.  
**With Hexarch**: `/authorize` request/response logs provide structured audit trail. Decision reason strings trace which policies fired. Policy evaluation is external and inspectable.

---

## What Hexarch Does Not Replace

### Identity and Access Management (IAM)
**Hexarch does not**: Authenticate users, verify credentials, or manage roles/permissions.  
**You still need**: OAuth, API keys, RBAC, or directory services to verify caller identity before reaching the orchestrator.  
**Why**: Hexarch assumes the caller has already authenticated. Authorization request context can include user identity, but Hexarch does not validate it.

### Network firewalls and access control lists
**Hexarch does not**: Block network traffic, enforce IP allowlists, or restrict outbound connections.  
**You still need**: Firewall rules, VPCs, security groups, or egress filtering to control network access.  
**Why**: Hexarch operates at the application layer. Network-level enforcement happens before requests reach the policy engine.

### Runtime sandboxing and process isolation
**Hexarch does not**: Execute code in isolated environments, constrain system calls, or prevent malicious execution.  
**You still need**: Containers, VMs, seccomp, AppArmor, or language-level sandboxes for untrusted code execution.  
**Why**: Hexarch evaluates policy and returns decisions. If the caller ignores the decision and proceeds with unsafe execution, Hexarch cannot prevent it.

### Input validation and sanitization
**Hexarch does not**: Validate JSON schema, sanitize SQL queries, or escape HTML entities in user input.  
**You still need**: Schema validation libraries, parameterized queries, and output encoding at the application layer.  
**Why**: Hexarch evaluates rule conditions against context fields. It does not inspect the content of those fields for injection attacks or malformed data.

### Business logic validation
**Hexarch does not**: Verify workflow correctness, detect infinite loops in flow graphs, or validate state machine transitions.  
**You still need**: Workflow analysis tools, static analysis, or formal verification for logic correctness.  
**Why**: Hexarch checks context against rules. If the context values are logically incorrect (e.g., `request_count` underreported), Hexarch cannot detect the error.

### Secrets management
**Hexarch does not**: Store API keys, rotate credentials, or encrypt sensitive data at rest.  
**You still need**: Vault, AWS Secrets Manager, or environment variable encryption for credential storage.  
**Why**: The `HEXARCH_API_TOKEN` is a shared secret for policy API access. Application secrets (OpenAI key, database password) remain the caller's responsibility.

### Application performance monitoring (APM)
**Hexarch does not**: Trace request latency, profile memory usage, or detect performance regressions.  
**You still need**: APM tools (Datadog, New Relic, Prometheus) to monitor orchestrator and downstream API performance.  
**Why**: Hexarch adds latency to the request path (5-50ms depending on deployment). APM tools measure this overhead and overall workflow execution time.

### Error recovery and circuit breaking
**Hexarch does not**: Retry failed `/authorize` requests, implement exponential backoff, or open circuits on repeated failures.  
**You still need**: Retry logic in the orchestrator or a circuit breaker library to handle transient policy engine failures.  
**Why**: If `/authorize` times out, the orchestrator decides whether to deny by default or allow with warning. Hexarch does not manage its own failover.

---

## Decision Matrix

| Capability | Hexarch Replaces | You Still Need |
|------------|------------------|----------------|
| Threshold enforcement before API calls | ✓ Ad hoc workflow conditionals | IAM for authentication |
| Model allowlist validation | ✓ Inline string comparisons | Input schema validation |
| Retry ceiling enforcement | ✓ Hard-coded loop limits | Circuit breaker for transient failures |
| Centralized policy for multiple workflows | ✓ Duplicate logic across flows | Network firewall rules |
| Pre-execution cost gating | ✓ Post-execution billing alerts | APM for latency monitoring |
| Audit trail of policy decisions | ✓ Manual compliance reviews | Secrets management for credentials |
| Deterministic allow/deny decisions | ✓ Probabilistic or manual approval | Runtime sandbox for untrusted code |

Hexarch operates in the authorization layer between authentication (IAM) and execution (workflow invocation). It does not replace infrastructure security, identity verification, or application correctness validation.
