# Deterministic Evaluation Example

## Identical Input → Identical Output

### Rule Definition
```json
{
  "name": "request_threshold",
  "rule_type": "threshold",
  "condition": {
    "field": "input.context.request_count",
    "op": "lte",
    "value": 5
  },
  "priority": 100
}
```

### Policy Definition
```json
{
  "name": "threshold_enforcement",
  "scope": "GLOBAL",
  "failure_mode": "FAIL_CLOSED",
  "rule_ids": ["a1b2c3d4"]
}
```

### Authorization Request (First Invocation)
```json
{
  "action": "call_provider",
  "resource": {
    "type": "api",
    "name": "openai.ChatCompletion"
  },
  "context": {
    "request_count": 3,
    "threshold": 5
  }
}
```

### Response (First Invocation)
```json
{
  "allowed": true,
  "decision": "ALLOW",
  "reason": null,
  "policies": [
    {
      "id": "policy-001",
      "name": "threshold_enforcement",
      "scope": "GLOBAL"
    }
  ]
}
```

### Authorization Request (Second Invocation)
```json
{
  "action": "call_provider",
  "resource": {
    "type": "api",
    "name": "openai.ChatCompletion"
  },
  "context": {
    "request_count": 3,
    "threshold": 5
  }
}
```

### Response (Second Invocation)
```json
{
  "allowed": true,
  "decision": "ALLOW",
  "reason": null,
  "policies": [
    {
      "id": "policy-001",
      "name": "threshold_enforcement",
      "scope": "GLOBAL"
    }
  ]
}
```

## Modified Rule → Different Deterministic Output

### Modified Rule Definition
```json
{
  "name": "request_threshold",
  "rule_type": "threshold",
  "condition": {
    "field": "input.context.request_count",
    "op": "lte",
    "value": 2
  },
  "priority": 100
}
```

### Authorization Request (Same Payload)
```json
{
  "action": "call_provider",
  "resource": {
    "type": "api",
    "name": "openai.ChatCompletion"
  },
  "context": {
    "request_count": 3,
    "threshold": 5
  }
}
```

### Response (With Modified Rule)
```json
{
  "allowed": false,
  "decision": "DENY",
  "reason": "policy_denied:a1b2c3d4-threshold_enforcement",
  "policies": [
    {
      "id": "policy-001",
      "name": "threshold_enforcement",
      "scope": "GLOBAL"
    }
  ]
}
```

## Verification

- **Identical context and rule** → `allowed: true` (both invocations)
- **Identical context, modified rule** → `allowed: false`
- **No random variation**: Response structure deterministic
- **Decision bound to rule state**: Changing `value: 5` to `value: 2` produces opposite decision for `request_count: 3`
