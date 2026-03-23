# Fail-Closed Behavior

## Network Failure: Policy Engine Unreachable

When the orchestrator cannot reach the `/authorize` endpoint, no policy decision is returned. The orchestrator must choose how to handle this failure.

### Scenario 1: Connection Timeout
```
POST http://localhost:8000/authorize
Connection timeout after 5000ms
```

### Scenario 2: Service Unavailable
```
POST http://localhost:8000/authorize
HTTP 503 Service Unavailable
```

### Scenario 3: Network Partition
```
POST http://localhost:8000/authorize
ECONNREFUSED: Connection refused
```

In all three cases, the orchestrator did not receive an authorization decision. The workflow must decide whether to proceed or halt.

## Recommended Integration Patterns

### Pattern 1: Deny-by-Default (Fail-Closed)

If the `/authorize` request fails (timeout, connection error, HTTP 5xx), treat the failure as DENY. Halt workflow execution.

**n8n Implementation**:
```json
{
  "name": "If Guardrails Reachable",
  "type": "n8n-nodes-base.if",
  "parameters": {
    "conditions": {
      "boolean": [
        {
          "value1": "={{$json.statusCode}}",
          "operation": "equal",
          "value2": 200
        }
      ]
    }
  }
}
```

If `statusCode !== 200`, route to an error output. Do not proceed with downstream API calls.

**Node-RED Implementation**:
```javascript
// In a switch node
if (msg.statusCode === 200 && msg.payload.allowed === true) {
    return [msg, null]; // Allow output
} else {
    return [null, msg]; // Deny output (covers both policy deny and network failure)
}
```

**Rationale**: When authorization cannot be verified, assume denial. This prevents unauthorized actions from executing during policy engine outages.

### Pattern 2: Allow-with-Warning (Fail-Open with Observability)

If the `/authorize` request fails, proceed with the downstream action but emit a warning signal for audit or alerting.

**n8n Implementation**:
```json
{
  "name": "If Guardrails Reachable",
  "type": "n8n-nodes-base.if",
  "parameters": {
    "conditions": {
      "boolean": [
        {
          "value1": "={{$json.statusCode}}",
          "operation": "equal",
          "value2": 200
        }
      ]
    }
  }
}
```

If `statusCode !== 200`, route to a logging node before proceeding to normal execution.

**Node-RED Implementation**:
```javascript
// In a function node before switch
if (msg.statusCode !== 200) {
    node.warn("Guardrails unreachable, proceeding with ALLOW assumption");
    msg.payload = { allowed: true, decision: "ALLOW_FALLBACK", reason: "guardrails_unavailable" };
}
return msg;
```

**Rationale**: When availability is more important than strict enforcement, allow execution to continue during policy engine outages but maintain audit visibility.

## Policy-Level Failure Mode (Distinct from Network Failure)

The `failure_mode` field in a policy definition controls what happens when a rule condition cannot be evaluated due to missing context fields.

### FAIL_CLOSED Policy
```json
{
  "name": "strict_threshold",
  "scope": "GLOBAL",
  "failure_mode": "FAIL_CLOSED",
  "rule_ids": ["rule-threshold-001"]
}
```

If the rule condition references `input.context.request_count` but the authorization request does not provide that field, the rule evaluation fails. Under FAIL_CLOSED, the policy contributes a DENY signal.

**Authorization Request (Missing Field)**:
```json
{
  "action": "call_provider",
  "resource": { "type": "api", "name": "provider" },
  "context": {}
}
```

**Response**:
```json
{
  "allowed": false,
  "decision": "DENY",
  "reason": "policy_denied:strict_threshold",
  "policies": [{"id": "policy-001", "name": "strict_threshold", "scope": "GLOBAL"}]
}
```

### FAIL_OPEN Policy
```json
{
  "name": "permissive_threshold",
  "scope": "GLOBAL",
  "failure_mode": "FAIL_OPEN",
  "rule_ids": ["rule-threshold-001"]
}
```

If the rule condition cannot be evaluated due to missing context, the policy contributes an ALLOW signal.

**Authorization Request (Missing Field)**:
```json
{
  "action": "call_provider",
  "resource": { "type": "api", "name": "provider" },
  "context": {}
}
```

**Response**:
```json
{
  "allowed": true,
  "decision": "ALLOW",
  "reason": null,
  "policies": [{"id": "policy-001", "name": "permissive_threshold", "scope": "GLOBAL"}]
}
```

## Distinction Summary

| Failure Type | Who Decides | Control Mechanism | Example |
|--------------|-------------|-------------------|---------|
| Network failure (policy engine unreachable) | Orchestrator | Switch/If node routing on HTTP status | Connection timeout → halt workflow |
| Rule evaluation failure (missing context field) | Policy engine | `failure_mode` in policy definition | Missing `request_count` with FAIL_CLOSED → DENY |

Both mechanisms are explicit. Neither produces ambiguous states.
