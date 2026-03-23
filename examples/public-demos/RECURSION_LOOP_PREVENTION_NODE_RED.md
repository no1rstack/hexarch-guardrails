# Recursion / Loop Prevention (Node-RED)

## Problem

Workflow recursion and repeated self-invocation can amplify API traffic before runtime signals are visible. If each iteration triggers more work, execution count can grow faster than expected. This demo applies a pre-execution policy check on each iteration and blocks continuation once recursion depth exceeds a fixed threshold.

## Flow Asset

- Import flow: `examples/public-demos/flows/recursion-loop-prevention-node-red.json`

The flow uses `Inject` + `Split` to simulate repeated invocations with depths `[1,2,3,4,5]`.

## Rule and Policy Requests

### Rule request

```http
POST /rules
Authorization: Bearer dev-token
X-Actor-Id: admin
Content-Type: application/json

{
  "name": "recursion-depth-limit",
  "rule_type": "CONSTRAINT",
  "description": "Allow only recursion_depth <= 3",
  "priority": 10,
  "enabled": true,
  "condition": {
    "field": "input.context.recursion_depth",
    "op": "lte",
    "value": 3
  }
}
```

### Policy request

```http
POST /policies
Authorization: Bearer dev-token
X-Actor-Id: admin
Content-Type: application/json

{
  "name": "recursion-prevention-policy",
  "description": "Block after recursion depth threshold",
  "enabled": true,
  "scope": "GLOBAL",
  "scope_value": null,
  "failure_mode": "FAIL_CLOSED",
  "rule_ids": ["38d6a5c6-2a22-40c9-b13f-ec07e7bb087f"]
}
```

## Authorization Payload Used by the Flow

```json
{
  "action": "call_provider",
  "resource": { "name": "workflow-self-call" },
  "context": {
    "provider_action": "invoke",
    "recursion_depth": 4,
    "invocation_count": 4
  }
}
```

## Real Responses (Captured)

```http
POST /authorize (recursion_depth=2)
200 OK
{
  "allowed": true,
  "decision": "ALLOW",
  "reason": null,
  "policies": ["f98e4b7c-644f-48f5-a537-2b3598c8fce4"]
}
```

```http
POST /authorize (recursion_depth=4)
200 OK
{
  "allowed": false,
  "decision": "DENY",
  "reason": "policy_denied:f98e4b7c-644f-48f5-a537-2b3598c8fce4",
  "policies": ["f98e4b7c-644f-48f5-a537-2b3598c8fce4"]
}
```

## Execution Outcome

- Depths `1..3` continue to downstream call.
- Depths `4..5` route to blocked path and stop before downstream execution.
