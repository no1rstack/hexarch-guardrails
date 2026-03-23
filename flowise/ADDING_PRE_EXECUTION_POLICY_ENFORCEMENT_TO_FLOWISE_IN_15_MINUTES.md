# Adding Pre-Execution Policy Enforcement to Flowise in 15 Minutes

## Problem

Agent builders make it easy to chain prompts, tools, and external API calls. They also make it easy to create cost amplification, recursive tool use, or sensitive actions before a human can intervene. Logs and dashboards are useful after the fact, but they are reactive controls.

In Flowise, the stronger pattern is a pre-execution policy gate: call Hexarch Guardrails before the provider or tool node runs, then branch deterministically on allow/deny.

## Why Flowise is a good fit

Flowise Agentflow V2 provides the exact building blocks needed for a policy gate:

- **Start Node** to initialize inputs and `$flow.state`
- **HTTP Node** to call `POST /authorize`
- **Condition Node** for deterministic true/false routing
- **LLM Node** or **Tool Node** to perform the guarded action only on allow
- **Direct Reply Node** to stop cleanly on deny

The Flowise docs also document `$flow.state` as the shared runtime state store across nodes in a single run, which makes it ideal for passing the authorization result to later steps.

## Architecture Pattern

Flow:

1. Start node collects user prompt and initializes Flow State keys.
2. HTTP node sends the prompt metadata, requested tool/provider action, and risk context to Hexarch `POST /authorize`.
3. HTTP node writes the parsed decision into `$flow.state`.
4. Condition node checks `{{ $flow.state.allowed }}`.
5. If `true`, continue to the LLM or Tool node.
6. If `false`, route to a Direct Reply node that explains the block.

## Minimal Demonstration

This folder includes copyable snippets for the key pieces:

- `flowise/snippets/authorize-request-body.json`
- `flowise/snippets/flow-state-example.json`

Because Flowise exports can change between versions, this demo is intentionally documented as a **node-by-node pattern** instead of claiming a universal importable export file.

## Step 1: Initialize Flow State in Start Node

Create these Flow State keys in the Start node:

- `userPrompt`
- `providerAction`
- `riskScore`
- `allowed`
- `denyReason`
- `authResponse`

Example values are in `flowise/snippets/flow-state-example.json`.

## Step 2: Configure the HTTP Node

Use the HTTP Node to call your Hexarch authorization endpoint.

Recommended configuration:

- **Method**: `POST`
- **URL**: `http://127.0.0.1:8099/authorize`
- **Headers**:
  - `Authorization: Bearer dev-token`
  - `Content-Type: application/json`
- **Body Type**: `JSON`
- **Body**: use the payload from `flowise/snippets/authorize-request-body.json`
- **Response Type**: `JSON`

### Example request body

```json
{
  "action": "invoke_provider",
  "resource": { "name": "llm-provider" },
  "context": {
    "provider_action": "{{ $flow.state.providerAction }}",
    "prompt": "{{ $flow.state.userPrompt }}",
    "risk_score": "{{ $flow.state.riskScore }}",
    "workflow": "flowise-pre-execution-gate"
  }
}
```

### Update Flow State from the HTTP Node

Write the following values into Flow State:

- `authResponse` ← full HTTP node response
- `allowed` ← `{{ httpNode.output.allowed }}`
- `denyReason` ← `{{ httpNode.output.reason }}`

## Step 3: Add the Condition Node

Set the Condition Node to evaluate:

- **Type**: `Boolean`
- **Value 1**: `{{ $flow.state.allowed }}`
- **Operation**: `equal`
- **Value 2**: `true`

This produces two branches:

- **true** → continue to LLM or Tool node
- **false** → route to a Direct Reply node

## Step 4: Guard the provider/tool step

Attach the `true` branch to one of:

- **LLM Node** if the guarded action is model inference
- **Tool Node** if the guarded action is a deterministic external tool/API call

Only this branch is allowed to create side effects.

## Step 5: Add a deny response path

Attach the `false` branch to a Direct Reply node with a message such as:

```text
Request blocked by Hexarch policy gate: {{ $flow.state.denyReason }}
```

This makes denial visible to the end user while preventing the provider/tool step from running.

## Example authorization policy

### Step 1: Create a threshold rule

```http
POST /rules
Authorization: Bearer dev-token
X-Actor-Id: admin
Content-Type: application/json

{
  "name": "flowise-risk-threshold",
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

### Step 2: Attach rule to a policy

```http
POST /policies
Authorization: Bearer dev-token
X-Actor-Id: admin
Content-Type: application/json

{
  "name": "flowise-pre-execution-risk-gate",
  "description": "Block provider call when risk score is over 5",
  "enabled": true,
  "scope": "GLOBAL",
  "scope_value": null,
  "failure_mode": "FAIL_CLOSED",
  "rule_ids": ["<RULE_ID_FROM_STEP_1>"]
}
```

## Before / After Behavior

### Without the Hexarch gate

The LLM or Tool node runs immediately when the flow reaches it.

### With the Hexarch gate

- `risk_score=3` → Condition node routes to the provider step
- `risk_score=7` → Condition node routes to the deny reply path

## Engineering Note

This is a deterministic branch-control pattern, not post-hoc error handling. The purpose is to decide **before** the side effect occurs. Flowise’s HTTP Node and Condition Node make this especially clean: authorization becomes just another explicit step in the graph, rather than something hidden in downstream code.

## Future expansion ideas

Once this basic gate is in place, you can extend the pattern with:

- **Human Input Node** on deny-or-review paths for approval workflows
- **Loop Node** plus Hexarch thresholds to stop recursive/tool amplification
- **Tool Node** protection for provider calls, webhooks, and sensitive admin actions
- **Shared `$flow.state`** fields for budget, actor identity, or environment metadata
