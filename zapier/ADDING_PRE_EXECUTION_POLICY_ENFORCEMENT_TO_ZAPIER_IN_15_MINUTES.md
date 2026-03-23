# Adding Pre-Execution Policy Enforcement to Zapier in 15 Minutes

## Problem

Zapier Zaps execute every action step automatically once the trigger fires. A Zap that calls an LLM, pushes to an API, or creates records in a database will do so unconditionally — there is no built-in way to ask a policy engine "should this run?" before the side-effecting step. Notifications and logging help, but they are reactive. The engineering goal is to block the Zap at the decision point, before any external action runs.

## Architecture Pattern

Hexarch Guardrails is evaluated as a Code step. The result is then enforced by a Filter step. Actions placed after the Filter only run on allow.

```
Trigger (Webhooks / Schedule / App event)
  └─ check_policy  (Code by Zapier — POST /authorize, returns allowed field)
       └─ Filter   (Zapier built-in — only continue if allowed is true)
            └─ invoke_provider  (your downstream action — skipped on deny)
```

1. Trigger fires with the event data.
2. `check_policy` Code step maps input fields, calls `POST /authorize` via `fetch`, returns the decision.
3. A Filter step checks if the `allowed` output field equals `true`.
4. Filter stops the Zap entirely when the decision is deny — downstream actions do not run.
5. Downstream actions run only when allowed.

## Why Zapier fits

- **Code step `inputData`**: maps fields from the trigger or previous steps into the code sandbox. No npm modules — only `fetch` (built-in) and the standard Node.js library are available. That is all this gate needs.
- **Filter step**: natively stops the Zap and records a clear "filtered out" run in Zap History when data fails the check. No custom logic required.
- **Paths**: for more complex routing (log deny reason, notify a Slack channel on deny, continue on allow), swap the Filter for a Paths step with two branches.
- All deny decisions appear in Zap History as filtered or errored runs — they are automatically logged without any additional steps.

## Minimal Demonstration

This repository contains a paste-ready code snippet:

- `zapier/snippets/check-policy-step.js` — Code by Zapier step: calls Hexarch `/authorize`, returns `allowed` and `decision`

The demo uses `risk_score=7` (denied) and `risk_score=3` (allowed) against a `threshold=5` rule. You replace those values with real fields from your trigger.

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
  "name": "zapier-risk-threshold",
  "rule_type": "CONSTRAINT",
  "description": "Deny when risk score exceeds the allowed threshold",
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
  "name": "zapier-pre-execution-gate",
  "description": "Block provider action when risk score is over 5",
  "enabled": true,
  "scope": "GLOBAL",
  "scope_value": null,
  "failure_mode": "FAIL_CLOSED",
  "rule_ids": ["<RULE_ID>"]
}
```

### Step 4: Build the Zap

**Trigger**: any trigger — Webhooks by Zapier (Catch Hook) works well for testing. The trigger fires with your input data.

**Action 1 — Code by Zapier (check_policy)**

1. In the Zap editor, click **+** to add an action.
2. Search for **Code by Zapier** → select **Run Javascript**.
3. In the **Input Data** section, add these key/value pairs (map values from your trigger):

| Key | Value (from trigger data) |
|---|---|
| `hexarchApiUrl` | `http://127.0.0.1:8099` (hardcode for local dev) |
| `hexarchApiToken` | `dev-token` (hardcode for local dev) |
| `action` | `invoke_provider` (or map from trigger) |
| `resourceName` | `llm-provider` (or map from trigger) |
| `providerAction` | `chat_completion` (or map from trigger) |
| `riskScore` | map the risk score field from your trigger |
| `threshold` | `5` (or map from trigger) |

4. In the **Code** field, paste the code from `zapier/snippets/check-policy-step.js`.
5. Click **Test step** to validate the connection.

**Action 2 — Filter**

1. Click **+** to add an action.
2. Search for **Filter** (built-in tool).
3. Set the filter rule:
   - Field: `allowed` (from the Code step output)
   - Condition: `(Text) Exactly matches`
   - Value: `true`
4. Test the filter. When `allowed` is `false` (deny), the filter shows "Zap would not have continued". When `true`, it shows "Zap would have continued".

**Action 3+ — your downstream actions**

Add your LLM call, API action, or record creation after the Filter. These steps only execute when the filter passes.

### Step 5: Test deny and allow

**Denied** — set `riskScore` input data to `7`:

- Code step output: `{ "allowed": "false", "decision": "DENY", "reason": "..." }`
- Filter: Zap stops here. Run appears in Zap History as "Filtered out".
- Downstream actions: not executed.

**Allowed** — set `riskScore` input data to `3`:

- Code step output: `{ "allowed": "true", "decision": "ALLOW" }`
- Filter: passes. Zap continues.
- Downstream actions: execute normally.

## Before and After

**Before adding the gate:**

- Every trigger event causes downstream actions to run.
- Cost and volume controls exist only in billing alerts or after-the-fact log review.
- There is no way to block a run based on context without modifying app-side logic.

**After adding the gate:**

- `check_policy` evaluates the context before any side-effecting action runs.
- Filter stops the Zap when the decision is deny — downstream steps never execute.
- All blocked runs are recorded in Zap History with the filter reason visible.
- All authorization decisions are logged by Hexarch with timestamp, actor, policy, and rule references.

## Suggested Extensions

**Use Paths instead of Filter for richer deny handling**

Replace the Filter step with a Paths step. In Path A (allow), run the downstream actions. In Path B (deny), send a Slack message, log to a spreadsheet, or call a Webhooks by Zapier action to notify a system.

```
check_policy
  └─ Paths
       ├─ Path A: allowed = true  → invoke_provider
       └─ Path B: allowed = false → notify_slack (or log to sheet)
```

**Log the deny reason**

The `check_policy` step exports a `reason` field from Hexarch. Map `reason` from the Code step output into your deny path action (Slack message, Google Sheets row, etc.) for an audit trail.

**Map real trigger fields**

Replace the hardcoded demo values in `inputData` with real fields from your Zapier trigger. For example, if your trigger brings in a `user_risk_score` field, map that as the value for the `riskScore` key in the Code step's Input Data.

**Scope policies per environment**

Set `"scope": "ACTOR"` and `"scope_value": "zapier-prod"` when creating the policy to target only production Zaps. Use a different policy for staging with a looser threshold.

**Point at a deployed Hexarch instance**

For production, replace `hexarchApiUrl` in the Input Data with your deployed Hexarch URL (HTTPS). Use an environment-scoped API token instead of `dev-token`.

## Engineering Note

The Filter step does not catch an exception or log a failure — it stops the Zap. Steps that appear after the Filter are never invoked when the filter condition is not met. This is the same outcome as `$.flow.exit()` in Pipedream: the downstream step function is never called, not just silently skipped.

The Code step uses `fetch` with a `try/catch`. If Hexarch is unreachable, the error is caught and `allowed` defaults to `"false"`. This mirrors Hexarch's own `failure_mode: FAIL_CLOSED` behavior: when the policy engine cannot be reached, the safe default is deny, not allow.
