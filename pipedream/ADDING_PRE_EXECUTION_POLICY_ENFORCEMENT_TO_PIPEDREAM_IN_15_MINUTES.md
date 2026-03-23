# Adding Pre-Execution Policy Enforcement to Pipedream in 15 Minutes

## Problem

Pipedream workflows execute each step immediately and in sequence. A workflow that calls an LLM, pushes to an external API, or triggers a cloud job starts spending money or producing side effects as soon as the step runs. Logging or alerting after the fact is reactive. The goal here is to block the downstream step **before** any external call is made, using a deterministic policy decision.

## Architecture Pattern

Hexarch Guardrails is evaluated as an early code step. If the decision is deny, `$.flow.exit()` ends the workflow immediately. No later steps run.

```
HTTP Trigger
  └─ check_policy  (Node.js — POST /authorize)
       └─ enforce  (Node.js — $.flow.exit() on deny)
            └─ invoke_provider  (your downstream call — only runs on allow)
```

1. HTTP trigger receives the workflow input.
2. `check_policy` step sends policy context to `POST /authorize`.
3. Hexarch evaluates policy rules and returns `ALLOW` or `DENY`.
4. `enforce` step calls `$.flow.exit()` on deny; issues a `403` HTTP response to the caller.
5. `invoke_provider` step only executes when allow.

## Why Pipedream fits

Pipedream's step model maps precisely to this pattern:

- Each step runs sequentially. A `$.flow.exit()` call in any step terminates all remaining steps immediately.
- Steps share data through `steps.step_name.$return_value`. The policy decision from `check_policy` is available directly in `enforce`.
- HTTP triggers expose a unique endpoint URL per workflow, so external systems can call the guarded workflow like a webhook.
- Secrets are stored as project-scoped environment variables and accessed via `process.env`, never hard-coded.
- The entire enforcement logic is two Node.js steps — no new infrastructure needed.

## Minimal Demonstration

This repository contains two ready-to-paste code steps:

- `pipedream/snippets/check-policy-step.js` — posts to `/authorize`, returns the decision
- `pipedream/snippets/enforce-step.js` — exits the workflow and sends a `403` on deny

The demo uses `risk_score=7` (denied) and `risk_score=3` (allowed) against a `threshold=5` rule.

### Step 1: Start Hexarch Guardrails

```sh
hexarch-ctl serve api \
  --host 127.0.0.1 \
  --port 8099 \
  --init-db \
  --api-token dev-token
```

### Step 2: Create a threshold rule

```http
POST /rules
Authorization: Bearer dev-token
X-Actor-Id: admin
Content-Type: application/json

{
  "name": "pipedream-risk-threshold",
  "rule_type": "CONSTRAINT",
  "description": "Deny when risk score exceeds allowed threshold",
  "priority": 10,
  "enabled": true,
  "condition": {
    "field": "input.context.risk_score",
    "op": "lte",
    "value": 5
  }
}
```

Save the returned `id` as `<RULE_ID>`.

### Step 3: Attach rule to a policy

```http
POST /policies
Authorization: Bearer dev-token
X-Actor-Id: admin
Content-Type: application/json

{
  "name": "pipedream-pre-execution-gate",
  "description": "Block provider call when risk score is over 5",
  "enabled": true,
  "scope": "GLOBAL",
  "scope_value": null,
  "failure_mode": "FAIL_CLOSED",
  "rule_ids": ["<RULE_ID>"]
}
```

### Step 4: Configure Pipedream environment variables

In your Pipedream workspace, go to **Settings → Environment Variables** and add:

| Variable | Value |
|---|---|
| `HEXARCH_API_URL` | `http://127.0.0.1:8099` |
| `HEXARCH_API_TOKEN` | `dev-token` |

For production, replace these with your real URL and a scoped API token.

### Step 5: Build the workflow in Pipedream

1. Create a new workflow and choose **HTTP / Webhook** as the trigger.
2. Pipedream generates a unique endpoint URL — note it for testing.
3. Add a **Node.js code step** named `check_policy`. Paste the code from `pipedream/snippets/check-policy-step.js`.
4. Add a second **Node.js code step** named `enforce`. Paste the code from `pipedream/snippets/enforce-step.js`.
5. Add your downstream step (LLM call, API call, cloud job) after `enforce`.
6. Deploy the workflow.

### Step 6: Test the gate

**Denied (risk_score=7):**

```sh
curl -X POST https://<your-endpoint>.m.pipedream.net \
  -H "Content-Type: application/json" \
  -d '{
    "action": "invoke_provider",
    "resource_name": "llm-provider",
    "provider_action": "chat_completion",
    "risk_score": 7,
    "threshold": 5
  }'
```

Expected response `403`:

```json
{
  "allowed": false,
  "decision": "DENY",
  "reason": "policy_denied: pipedream-pre-execution-gate",
  "message": "Request blocked by pre-execution policy gate"
}
```

**Allowed (risk_score=3):**

```sh
curl -X POST https://<your-endpoint>.m.pipedream.net \
  -H "Content-Type: application/json" \
  -d '{
    "action": "invoke_provider",
    "resource_name": "llm-provider",
    "provider_action": "chat_completion",
    "risk_score": 3,
    "threshold": 5
  }'
```

Workflow continues past the `enforce` step and reaches your downstream step.

## Before and After

**Before adding the gate:**

- Pipedream workflow executes downstream steps unconditionally.
- An LLM call, external API, or cloud job runs for every request regardless of context.
- Cost and risk controls exist only in post-run logs or billing alerts.

**After adding the gate:**

- `check_policy` evaluates the request context before any side-effecting step runs.
- `enforce` terminates the workflow immediately on deny via `$.flow.exit()`.
- Downstream steps are unreachable on deny — not just skipped, but never invoked.
- All decisions are logged by Hexarch with timestamp, actor, policy, and rule references.

## Suggested Extensions

**Pass context from upstream steps**

If a previous step in your workflow computes a risk score or classification, pass it directly into the `check_policy` payload instead of reading from the trigger body.

```js
const riskScore = steps.classify.$return_value.risk_score;
```

**Extract policy decision for later steps**

The `check_policy` step exports the full Hexarch response. Downstream steps can access any field:

```js
const authDecision = steps.check_policy.$return_value;
console.log(authDecision.policy_id, authDecision.allowed_at);
```

**Guard multiple steps with one policy**

Call Hexarch once at the start of the workflow and check `steps.check_policy.$return_value.allowed` in any subsequent conditional. One authorization call gates all risky steps in the same execution.

**Scope policies to actors or environments**

Pass a `scope_value` when creating the policy (`"scope": "ACTOR"`, `"scope_value": "pipedream-prod"`) to target only production workflows.

**Use $.respond() for structured error envelopes**

The `enforce` step can return structured JSON errors that match whatever format your calling system expects — change the shape of the `body` in `$.respond()`.

**Deploy Hexarch on the same cloud as Pipedream**

For production, deploy Hexarch to a cloud host that Pipedream can reach over HTTPS. Update `HEXARCH_API_URL` to the public URL. Apply network controls (IP allowlist, TLS mutual auth) as needed.

## Engineering Note

This is not error handling — it is deterministic prevention. `$.flow.exit()` does not catch an exception or log a failure. It halts the execution engine before the downstream step function is ever called. There is no race between the guard and the guarded step. The enforcement contract is: if Hexarch returns deny, the next step does not run — provably and without exception.

Hexarch's `failure_mode: FAIL_CLOSED` reinforces this: if the policy evaluation itself encounters an error (network failure, misconfiguration), the default decision is deny, not allow. The safe default is to block.
