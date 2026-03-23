# Adding Pre-Execution Policy Enforcement to Postman in 15 Minutes

## Problem

API clients are often used as if they are harmless test harnesses, but they can trigger real side effects: production deploy hooks, model-provider spend, destructive admin operations, or high-volume replay traffic. Observability helps after the call. The stronger control is to decide before the call is sent.

In Postman, the clean pattern is to call Hexarch Guardrails first, inspect the allow/deny decision, and only then send the risky downstream request.

## Architecture Pattern

Postman asks Hexarch `POST /authorize` for a decision before the protected request is executed.

Pattern:

1. Create a rule that describes the threshold or constraint.
2. Attach the rule to a policy.
3. Call `POST /authorize` with contextual metadata about the pending action.
4. If Hexarch returns allow, continue to the external call.
5. If Hexarch returns deny, stop before side effects occur.

## Minimal Demonstration

This repository includes importable Postman assets:

- `postman/collections/hexarch-pre-execution-policy-gate-demo.postman_collection.json`
- `postman/environments/hexarch-local.postman_environment.json`

The collection walks through a full local demo:

1. Create a threshold rule
2. Create a policy referencing that rule
3. Send a denied authorization request
4. Send an allowed authorization request

The default demo values intentionally show both paths:

- `riskScoreDenied=7`
- `riskScoreAllowed=3`
- `threshold=5`

## Import Steps

1. Open Postman.
2. Import the collection file from `postman/collections/`.
3. Import the environment file from `postman/environments/`.
4. Select the `Hexarch Local Dev` environment.
5. Start the Hexarch API locally.
6. Run the requests in order.

## Local API setup

Run the local API with a bearer token:

```bash
hexarch-ctl serve api --host 127.0.0.1 --port 8099 --init-db --api-token dev-token
```

If `hexarch-ctl` resolves to the wrong interpreter on Windows, use:

```bash
python -m hexarch_cli serve api --host 127.0.0.1 --port 8099 --init-db --api-token dev-token
```

## Request Flow

### Step 1: Create threshold rule

The collection creates a rule like this:

```json
{
  "name": "postman-risk-threshold",
  "rule_type": "CONSTRAINT",
  "description": "Deny provider invocation when risk score exceeds threshold",
  "priority": 10,
  "enabled": true,
  "condition": {
    "field": "input.context.risk_score",
    "op": "lte",
    "value": 5
  }
}
```

The response test stores the rule id into the environment as `ruleId`.

### Step 2: Create policy

The next request creates a fail-closed policy using `{{ruleId}}`:

```json
{
  "name": "postman-pre-execution-gate",
  "description": "Block provider call when risk score is over threshold",
  "enabled": true,
  "scope": "GLOBAL",
  "scope_value": null,
  "failure_mode": "FAIL_CLOSED",
  "rule_ids": ["{{ruleId}}"]
}
```

The response test stores the policy id into the environment as `policyId`.

### Step 3: Send denied authorization request

The collection then sends:

```json
{
  "action": "invoke_provider",
  "resource": { "name": "llm-provider" },
  "context": {
    "client": "postman",
    "provider_action": "chat_completion",
    "risk_score": 7,
    "threshold": 5,
    "workflow": "postman-pre-execution-policy-gate-demo"
  }
}
```

Expected result:

```json
{
  "allowed": false,
  "decision": "DENY",
  "reason": "policy_denied:postman-pre-execution-gate"
}
```

### Step 4: Send allowed authorization request

The final request repeats the authorization call with `risk_score=3`.

Expected result:

```json
{
  "allowed": true,
  "decision": "ALLOW",
  "reason": null
}
```

## Before / After Behavior

### Without the Hexarch pre-check

Postman sends the expensive or risky request immediately.

### With the Hexarch pre-check

Postman first asks for an allow/deny decision. The protected request should only be sent when the decision is allow.

A practical way to use this in a real collection is:

- put the guard request in a folder or workflow step before the risky request
- use tests to store `allowed`
- gate follow-on requests using collection runner logic, Flows, or human/operator choice

## Engineering Note

Postman is not just an API client; for many teams it becomes an operational control surface. That makes it a good place to demonstrate guardrails. The key point is not merely that Postman can call Hexarch — it is that the authorization decision becomes a first-class step in the request workflow before external side effects begin.

## Suggested extensions

Once this baseline works, you can extend the collection with:

- a guarded provider call request that only runs after a successful allow decision
- budget or tenant-aware context fields
- collection tests that fail loudly when `allowed !== true`
- team workspaces with environment-scoped tokens for staging vs production
