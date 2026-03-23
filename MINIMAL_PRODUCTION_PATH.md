# Minimal Path to Production

This guide defines the minimum safe steps for deploying Hexarch Guardrails to production. Follow this path for a single workflow with pre-execution policy enforcement.

## Step 1: Deploy Service

### Topology Recommendation

For initial production deployment, co-locate Hexarch with the orchestrator (n8n, Node-RED, custom service) to minimize network latency. Deploy as a container or process on the same host.

**Deployment command** (Docker):
```bash
docker run -d \
  --name hexarch-guardrails \
  -p 8000:8000 \
  -e DATABASE_URL="sqlite:///data/hexarch.db" \
  -e HEXARCH_API_TOKEN="your-secure-token-here" \
  -e HEXARCH_BOOTSTRAP_ALLOW="false" \
  -v /var/lib/hexarch:/data \
  hexarch/guardrails:latest
```

**Environment variables**:
- `DATABASE_URL`: SQLite file path or PostgreSQL connection string.
- `HEXARCH_API_TOKEN`: Shared secret for API authentication. Generate with `openssl rand -hex 32`.
- `HEXARCH_BOOTSTRAP_ALLOW`: Set to `false` for production (deny by default until policies are defined).

**Health check**:
```bash
curl -f http://localhost:8000/health || exit 1
```

## Step 2: Define First Rule and Policy

Start with one threshold rule to prevent runaway execution.

### Create Rule

**File**: `production-threshold-rule.json`
```json
{
  "name": "daily_request_limit_production",
  "rule_type": "threshold",
  "condition": {
    "field": "input.context.daily_requests",
    "op": "lte",
    "value": 100
  },
  "priority": 100
}
```

**Deploy rule**:
```bash
RULE_ID=$(curl -s -X POST http://localhost:8000/rules \
  -H "Authorization: Bearer $HEXARCH_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d @production-threshold-rule.json | jq -r '.id')

echo "Rule ID: $RULE_ID"
```

Save `$RULE_ID` for policy binding.

### Create Policy

**File**: `production-threshold-policy.json`
```json
{
  "name": "daily_limit_enforcement",
  "scope": "GLOBAL",
  "failure_mode": "FAIL_CLOSED",
  "rule_ids": ["<RULE_ID_HERE>"]
}
```

Replace `<RULE_ID_HERE>` with the value from the previous step.

**Deploy policy**:
```bash
curl -X POST http://localhost:8000/policies \
  -H "Authorization: Bearer $HEXARCH_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d @production-threshold-policy.json
```

## Step 3: Enforce Fail-Closed Integration Pattern

Configure the orchestrator to halt execution if `/authorize` returns DENY or if the policy engine is unreachable.

### n8n Integration

Add three nodes after the workflow trigger:

1. **HTTP Request** node:
   - Method: POST
   - URL: `http://localhost:8000/authorize`
   - Authentication: Header Auth with `Authorization: Bearer <token>`
   - Body: JSON with `action`, `resource`, `context`

2. **If** node:
   - Condition: `{{$json.allowed}} === true`
   - True branch: Continue to downstream API
   - False branch: Route to error handler

3. **Function** node (on False branch):
   - Code: `throw new Error('Policy denied: ' + $json.reason);`

### Node-RED Integration

Add three nodes after the inject trigger:

1. **Function** node (Build /authorize request):
```javascript
msg.url = "http://localhost:8000/authorize";
msg.method = "POST";
msg.headers = {
    "Authorization": "Bearer " + env.get("HEXARCH_API_TOKEN"),
    "Content-Type": "application/json"
};
msg.payload = {
    action: "invoke_api",
    resource: {type: "api", name: "external_service"},
    context: {daily_requests: flow.get("request_count") || 0}
};
return msg;
```

2. **HTTP Request** node:
   - Method: Use `msg.method`
   - URL: Use `msg.url`
   - Return: Parsed JSON object

3. **Switch** node:
   - Property: `msg.payload.allowed`
   - `== true`: Route to downstream API
   - `otherwise`: Route to error output

## Step 4: Add Logging

Log all `/authorize` responses for audit and debugging.

### n8n Logging Node

Add a **Function** node after receiving the `/authorize` response:
```javascript
console.log(JSON.stringify({
  timestamp: new Date().toISOString(),
  decision: $json.decision,
  allowed: $json.allowed,
  reason: $json.reason,
  policies: $json.policies
}));
return $input.all();
```

### Node-RED Logging Node

Add a **Debug** node with output set to complete message object. For structured logging, add a **Function** node:
```javascript
const logEntry = {
  timestamp: new Date().toISOString(),
  decision: msg.payload.decision,
  allowed: msg.payload.allowed,
  reason: msg.payload.reason,
  policies: msg.payload.policies
};
node.log(JSON.stringify(logEntry));
return msg;
```

Forward logs to centralized logging infrastructure (Elasticsearch, Splunk, CloudWatch) for retention and analysis.

## Step 5: Add Monitoring Metric

Track authorization success and deny rates to detect policy enforcement anomalies.

### Metric Collection

Instrument the orchestrator or log aggregation layer to emit:

- `hexarch.authorize.allow` (counter): Incremented when `allowed: true`.
- `hexarch.authorize.deny` (counter): Incremented when `allowed: false`.
- `hexarch.authorize.error` (counter): Incremented when `/authorize` request fails (network error, HTTP 5xx).

### Example (Prometheus format)

In a monitoring sidecar or log parser:
```
# HELP hexarch_authorize_allow_total Total ALLOW decisions
# TYPE hexarch_authorize_allow_total counter
hexarch_authorize_allow_total 1247

# HELP hexarch_authorize_deny_total Total DENY decisions
# TYPE hexarch_authorize_deny_total counter
hexarch_authorize_deny_total 53

# HELP hexarch_authorize_error_total Total authorization request errors
# TYPE hexarch_authorize_error_total counter
hexarch_authorize_error_total 2
```

### Alert Threshold

Set alert if `deny_rate > 10%` of total requests or if `error_rate > 1%`. Both signal misaligned policies or service degradation.

## Step 6: Validate with Test Payload

Before connecting the workflow to production data, send test payloads to verify policy behavior.

### Test Allow Scenario

```bash
curl -X POST http://localhost:8000/authorize \
  -H "Authorization: Bearer $HEXARCH_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "invoke_api",
    "resource": {"type": "api", "name": "test_service"},
    "context": {"daily_requests": 50}
  }'
```

**Expected response**:
```json
{
  "allowed": true,
  "decision": "ALLOW",
  "reason": null,
  "policies": [...]
}
```

### Test Deny Scenario

```bash
curl -X POST http://localhost:8000/authorize \
  -H "Authorization: Bearer $HEXARCH_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "invoke_api",
    "resource": {"type": "api", "name": "test_service"},
    "context": {"daily_requests": 150}
  }'
```

**Expected response**:
```json
{
  "allowed": false,
  "decision": "DENY",
  "reason": "policy_denied:daily_limit_enforcement",
  "policies": [...]
}
```

If both responses match expectations, policy enforcement is operational.

## Step 7: Rollout Guidance

Deploy incrementally to minimize risk.

### Phase 1: Non-Production Environment (1-3 days)

- Deploy Hexarch and policy to staging/dev environment.
- Connect workflow and run full test suite.
- Verify: ALLOW and DENY paths route correctly, logs capture decisions, metrics increment.

### Phase 2: Production Deployment with Permissive Policy (1-2 days)

- Deploy to production with initial policy threshold set **above** expected usage (e.g., `value: 10000` if typical daily usage is 100).
- Monitor deny rate. Should be near zero.
- If deny rate > 0%, investigate context field values and adjust threshold.

### Phase 3: Production Deployment with Enforcement Policy (ongoing)

- Lower threshold to target value (e.g., `value: 100`).
- Monitor deny rate and error logs for 48 hours.
- If deny rate aligns with expectations and no false positives occur, enforcement is stable.

### Rollback Plan

If policy enforcement causes unexpected denials:

1. Increase threshold value in rule definition.
2. POST updated rule to `/rules/<rule_id>` (if API supports updates) or create new rule and update policy binding.
3. Verify ALLOW rate returns to expected baseline.

Alternatively, set policy `failure_mode: "FAIL_OPEN"` temporarily to allow execution while investigating rule conditions.

## Summary Checklist

- [ ] Deploy Hexarch service with health check
- [ ] Create threshold rule and FAIL_CLOSED policy
- [ ] Integrate fail-closed pattern in orchestrator (if denied or unreachable → halt)
- [ ] Add logging for all `/authorize` responses
- [ ] Emit allow/deny/error metrics
- [ ] Validate with test payloads (allow and deny scenarios)
- [ ] Rollout to non-prod, then prod with permissive policy, then enforce

This path provides operational safety with incremental validation.
