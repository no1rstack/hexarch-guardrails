# Adding Pre-Execution Policy Enforcement to Langflow in 15 Minutes

## Problem

Agent builders are excellent at turning one user prompt into many downstream actions: model calls, tool calls, retriever fan-out, or external API requests. That same power creates a control problem. A flow can spend money, invoke tools, or trigger sensitive side effects before an operator can intervene.

The stronger pattern is a pre-execution policy gate: ask Hexarch Guardrails for an allow/deny decision before the LLM, provider, or tool step runs.

## Why Langflow is a good fit

Langflow provides two clean ways to implement this pattern:

1. **Native API Request component** for a no-code HTTP call to Hexarch.
2. **Custom component** for a reusable `Hexarch Authorize` building block.

The official docs confirm that:

- flows are DAGs executed in dependency order
- the **API Request** component returns a `Data` object containing the HTTP response
- **Run Flow** can be used to compose guarded subflows
- custom components can expose typed inputs/outputs and optional Tool Mode

That makes Langflow a very good fit for deterministic gating before a risky step.

## Architecture Pattern

### Option A: Native component flow

Use these nodes:

1. `Chat Input` or `Text Input`
2. `API Request`
3. `Parser` or simple downstream data extraction
4. guarded `Agent`, `Model`, `Tool`, or `Run Flow`
5. `Chat Output` or `Text Output`

High-level sequence:

1. User input enters the flow.
2. `API Request` sends a JSON authorization payload to Hexarch `POST /authorize`.
3. The response is inspected for `allowed=true` or `allowed=false`.
4. Only the allow path reaches the expensive/sensitive node.
5. The deny path returns a clear refusal message.

### Option B: Custom component flow

Create a reusable custom component named `Hexarch Authorize`.

This component:

- accepts `api_url`, `api_token`, `action`, `resource_name`, `provider_action`, and `risk_score`
- sends the authorization request to Hexarch
- returns structured `Data`
- can later be upgraded to Tool Mode for agent use

A starter implementation is included in:

- `langflow/snippets/hexarch_authorize_component.md`

## Minimal Demonstration

This folder includes copyable assets:

- `langflow/snippets/api-request-body.json`
- `langflow/snippets/hexarch_authorize_component.md`

The safest version-stable demo is the native `API Request` approach, because Langflow flow export formats and component versions can drift between releases.

## Step 1: Start Hexarch locally

Run the local API with a bearer token:

```bash
hexarch-ctl serve api --host 127.0.0.1 --port 8099 --init-db --api-token dev-token
```

If `hexarch-ctl` resolves to the wrong interpreter on Windows, use:

```bash
python -m hexarch_cli serve api --host 127.0.0.1 --port 8099 --init-db --api-token dev-token
```

## Step 2: Create a threshold rule

```http
POST /rules
Authorization: Bearer dev-token
X-Actor-Id: admin
Content-Type: application/json

{
  "name": "langflow-risk-threshold",
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

## Step 3: Attach the rule to a policy

```http
POST /policies
Authorization: Bearer dev-token
X-Actor-Id: admin
Content-Type: application/json

{
  "name": "langflow-pre-execution-gate",
  "description": "Block provider call when risk score is over 5",
  "enabled": true,
  "scope": "GLOBAL",
  "scope_value": null,
  "failure_mode": "FAIL_CLOSED",
  "rule_ids": ["<RULE_ID_FROM_STEP_2>"]
}
```

## Step 4: Configure Langflow with the native API Request component

Add an `API Request` component and configure it like this:

- **Mode**: `URL`
- **URL**: `http://127.0.0.1:8099/authorize`
- **Method**: `POST`
- **Headers**:
  - `Authorization: Bearer dev-token`
  - `Content-Type: application/json`
- **Body**: use `langflow/snippets/api-request-body.json`
- **Include HTTPx Metadata**: optional, but useful while debugging
- **Follow Redirects**: leave disabled unless you trust the target server

### Example request body

```json
{
  "action": "invoke_provider",
  "resource": { "name": "llm-provider" },
  "context": {
    "client": "langflow",
    "provider_action": "chat_completion",
    "risk_score": 7,
    "threshold": 5,
    "workflow": "langflow-pre-execution-policy-gate-demo"
  }
}
```

Because the API Request component returns a `Data` object, the response can be inspected by downstream components before the sensitive step executes.

## Step 5: Build the allow / deny split

There are two practical ways to branch:

### Simple path for demos

- Use one flow for the **guard check**.
- If the returned data says `allowed=false`, stop and return a denial message.
- If `allowed=true`, proceed to the expensive node.

### Reusable path for larger systems

- Put the guard logic in its own Langflow flow.
- Use **Run Flow** from your main agent/application flow.
- Reuse the same guard subflow for multiple agents or tools.

This keeps the authorization behavior centralized instead of re-copying HTTP settings across many flows.

## Example deny response

```json
{
  "allowed": false,
  "decision": "DENY",
  "reason": "policy_denied:langflow-pre-execution-gate"
}
```

## Example allow response

```json
{
  "allowed": true,
  "decision": "ALLOW",
  "reason": null
}
```

## Optional: Custom component approach

If you want a cleaner UX than manually wiring one HTTP request per flow, use the sample custom component starter in `langflow/snippets/hexarch_authorize_component.md`.

This is useful when:

- you want one reusable Hexarch node across many flows
- you want a more descriptive Langflow-native component in the canvas
- you want to evolve the guard into Tool Mode for agents later

The Langflow docs confirm that custom components can:

- inherit from `Component`
- define typed inputs and outputs
- expose multiple outputs when needed
- use `tool_mode=True` on supported inputs
- be loaded via `LANGFLOW_COMPONENTS_PATH`

## Before / After Behavior

### Without the guard

The model or tool node runs as soon as the flow reaches it.

### With the guard

- `risk_score=3` → authorization returns allow, flow continues
- `risk_score=7` → authorization returns deny, flow stops before the sensitive node

## Engineering Note

This is not post-hoc logging or failure handling. The entire purpose is deterministic pre-side-effect control. Langflow’s DAG execution model and API Request component make it straightforward to insert an authorization checkpoint in front of an LLM, agent, provider, or tool step.

## Suggested extensions

Once this baseline works, you can extend it with:

- a dedicated **guard subflow** called through `Run Flow`
- a reusable **Hexarch Authorize** custom component
- agent integration where only guarded tool paths are exposed
- environment-specific tokens and risk thresholds for staging vs production
