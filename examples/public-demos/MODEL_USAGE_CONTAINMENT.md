# Model Usage Containment

## Objective

Constrain model invocation requests before execution by enforcing an approved model list and a token ceiling through `POST /authorize`.

## Example Rule + Policy JSON

- Rule (model allowlist): `examples/public-demos/model-containment-rule-allowlist.json`
- Rule (token ceiling): `examples/public-demos/model-containment-rule-token-ceiling.json`
- Policy (bind both rules): `examples/public-demos/model-containment-policy.json`

## Requests and Responses (Captured)

### Rule creation response (model allowlist)

```json
{
  "id": "d3266023-4c45-4195-b4a5-a4fbe93e1c33",
  "name": "model-allowlist",
  "description": "Allow only approved models",
  "rule_type": "CONSTRAINT",
  "priority": 10,
  "enabled": true,
  "condition": {
    "field": "input.context.model",
    "op": "in",
    "value": ["gpt-4o-mini", "llama3"]
  }
}
```

### Rule creation response (token ceiling)

```json
{
  "id": "b5b90a5c-67b1-4054-9398-1745c989492b",
  "name": "token-ceiling",
  "description": "Allow only tokens_requested <= 4000",
  "rule_type": "CONSTRAINT",
  "priority": 20,
  "enabled": true,
  "condition": {
    "field": "input.context.tokens_requested",
    "op": "lte",
    "value": 4000
  }
}
```

### Policy creation response

```json
{
  "id": "29c75d32-db50-426e-821b-cd0da3b6f66b",
  "name": "model-usage-containment-policy",
  "description": "Restrict model and token usage",
  "scope": "GLOBAL",
  "scope_value": null,
  "enabled": true,
  "failure_mode": "FAIL_CLOSED",
  "rule_ids": [
    "b5b90a5c-67b1-4054-9398-1745c989492b",
    "d3266023-4c45-4195-b4a5-a4fbe93e1c33"
  ]
}
```

### Allow response

Request context:

```json
{
  "action": "call_provider",
  "resource": { "name": "llm" },
  "context": {
    "provider_action": "generate",
    "model": "gpt-4o-mini",
    "tokens_requested": 2000
  }
}
```

Response:

```json
{
  "allowed": true,
  "decision": "ALLOW",
  "reason": null,
  "policies": ["29c75d32-db50-426e-821b-cd0da3b6f66b"]
}
```

### Deny response (disallowed model)

Request context:

```json
{
  "action": "call_provider",
  "resource": { "name": "llm" },
  "context": {
    "provider_action": "generate",
    "model": "gpt-4.1",
    "tokens_requested": 2000
  }
}
```

Response:

```json
{
  "allowed": false,
  "decision": "DENY",
  "reason": "policy_denied:29c75d32-db50-426e-821b-cd0da3b6f66b",
  "policies": ["29c75d32-db50-426e-821b-cd0da3b6f66b"]
}
```

### Deny response (token ceiling exceeded)

```json
{
  "allowed": false,
  "decision": "DENY",
  "reason": "policy_denied:29c75d32-db50-426e-821b-cd0da3b6f66b",
  "policies": ["29c75d32-db50-426e-821b-cd0da3b6f66b"]
}
```
