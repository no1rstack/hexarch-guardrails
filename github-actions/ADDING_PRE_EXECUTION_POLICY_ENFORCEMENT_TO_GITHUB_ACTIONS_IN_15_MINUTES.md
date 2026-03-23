# Adding Pre-Execution Policy Enforcement to GitHub Actions in 15 Minutes

## Problem

CI/CD pipelines can create high-cost or high-risk side effects before a human notices. A workflow may deploy to production, trigger a costly model evaluation, rotate secrets, or fan out cloud jobs immediately after a push. Logs and alerts are useful, but they are reactive controls — they tell you what already happened.

A pre-execution policy gate moves the decision point in front of the side effect. GitHub Actions asks Hexarch Guardrails for an allow/deny decision before running the risky step.

## Architecture Pattern

GitHub Actions calls `POST /authorize` before the guarded job step. If Hexarch returns allow, the workflow continues. If Hexarch returns deny, the workflow exits before deployment or external calls begin.

Pattern:

1. Workflow starts from manual dispatch, push, or schedule.
2. Guard step posts policy context to `POST /authorize`.
3. Hexarch evaluates policy and returns `ALLOW` or `DENY`.
4. Workflow continues only when the guard decision is allow.
5. Deployment or provider call is skipped on deny.

## Minimal Demonstration

This repository includes a sample workflow:

- `github-actions/workflows/hexarch-pre-deploy-policy-gate-demo.yml`

It demonstrates a guarded deployment decision using a simple risk score. The default demo configuration uses `risk_score=7` and `threshold=5`, so the deploy step is blocked by design on first run.

### Step 1: Create a threshold rule

```http
POST /rules
Authorization: Bearer dev-token
X-Actor-Id: admin
Content-Type: application/json

{
  "name": "github-actions-risk-threshold",
  "rule_type": "CONSTRAINT",
  "description": "Deny deploy when risk score exceeds threshold",
  "priority": 10,
  "enabled": true,
  "condition": {
    "field": "input.context.risk_score",
    "op": "lte",
    "value": 5
  }
}
```

### Step 2: Attach rule to a policy

```http
POST /policies
Authorization: Bearer dev-token
X-Actor-Id: admin
Content-Type: application/json

{
  "name": "github-actions-pre-deploy-gate",
  "description": "Block deployment when risk score is over 5",
  "enabled": true,
  "scope": "GLOBAL",
  "scope_value": null,
  "failure_mode": "FAIL_CLOSED",
  "rule_ids": ["<RULE_ID_FROM_STEP_1>"]
}
```

### Step 3: Authorization payload sent by GitHub Actions

```json
{
  "action": "deploy_release",
  "resource": { "name": "production-environment" },
  "context": {
    "workflow": "hexarch-pre-deploy-policy-gate-demo",
    "branch": "main",
    "environment": "production",
    "risk_score": 7,
    "threshold": 5
  }
}
```

### Example rejection response

```json
{
  "allowed": false,
  "decision": "DENY",
  "reason": "policy_denied:github-actions-pre-deploy-gate",
  "policies": ["github-actions-pre-deploy-gate"]
}
```

## Before / After Behavior

### Without Guardrails pre-check

The deployment step runs as soon as the workflow reaches it.

```text
Build complete
Deploying to production...
Deployment finished
```

### With Guardrails pre-check

The workflow performs the policy call first. At `risk_score=3`, deployment is allowed. At `risk_score=7`, deployment is blocked before the deploy command runs.

```json
{
  "allowed": true,
  "decision": "ALLOW",
  "reason": null,
  "policies": ["github-actions-pre-deploy-gate"]
}
```

```json
{
  "allowed": false,
  "decision": "DENY",
  "reason": "policy_denied:github-actions-pre-deploy-gate",
  "policies": ["github-actions-pre-deploy-gate"]
}
```

## Sample GitHub Secrets

Set these in your repository or environment secrets:

- `HEXARCH_API_URL` — e.g. `http://127.0.0.1:8099`
- `HEXARCH_API_TOKEN` — bearer token used for `POST /authorize`

## Engineering Note

This pattern is a pre-side-effect gate. It is not equivalent to a failing deploy after steps already started, and it is not equivalent to post-deploy monitoring. The purpose is deterministic branch control before the risky action executes.
