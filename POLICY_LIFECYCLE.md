# Policy Lifecycle

Policy enforcement systems require operational governance to avoid configuration drift, stale rules, and unintended denial cascades. This document defines a minimal lifecycle for Hexarch policy management.

## Rule Creation

Rules define individual conditions. Each rule has:

- `name`: Unique identifier within the rule set.
- `rule_type`: Classification label (e.g., `threshold`, `allowlist`, `structural`).
- `condition`: JSON object with `field`, `op`, and `value`.
- `priority`: Integer for evaluation ordering (higher = evaluated first).

**Creation workflow**:
1. Define the context field to evaluate (`input.context.request_count`).
2. Choose the operator (`lte`, `gte`, `in`, `equals`).
3. Set the comparison value (integer, string, array).
4. Assign a priority (default: 100).
5. POST to `/rules` with rule definition.

**Example**:
```bash
curl -X POST http://localhost:8000/rules \
  -H "Authorization: Bearer $HEXARCH_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "daily_request_limit",
    "rule_type": "threshold",
    "condition": {
      "field": "input.context.daily_requests",
      "op": "lte",
      "value": 1000
    },
    "priority": 100
  }'
```

Save the returned `rule_id` for policy binding.

## Policy Grouping

Policies bind multiple rules with shared scope and failure mode. Each policy has:

- `name`: Human-readable policy identifier.
- `scope`: Enforcement boundary (GLOBAL, ORGANIZATION, TEAM, USER, RESOURCE).
- `failure_mode`: Behavior on rule evaluation error (FAIL_CLOSED, FAIL_OPEN).
- `rule_ids`: Array of rule identifiers to evaluate.

**Grouping criteria**:
- Rules enforcing the same operational boundary (e.g., all cost containment rules).
- Rules requiring identical failure behavior (e.g., all production rules use FAIL_CLOSED).
- Rules evaluated at the same scope (e.g., all TEAM-scoped rules for engineering).

**Example**:
```bash
curl -X POST http://localhost:8000/policies \
  -H "Authorization: Bearer $HEXARCH_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "cost_containment_policy",
    "scope": "ORGANIZATION",
    "failure_mode": "FAIL_CLOSED",
    "rule_ids": ["rule-daily-limit", "rule-token-ceiling"]
  }'
```

## Versioning Expectations

Hexarch does not enforce semantic versioning of rules or policies. Rule updates modify in-place. Policy updates affect all subsequent `/authorize` calls immediately.

**Version control pattern**:
1. Store rule and policy definitions in version-controlled JSON files.
2. Tag files with version identifiers (`v1.0.0-daily-limit-rule.json`).
3. Deploy to Hexarch via API POST on environment promotion.
4. Record deployment timestamp and rule/policy IDs in audit log.

**Example file structure**:
```
policies/
  v1.0.0/
    cost-containment-rules.json
    cost-containment-policy.json
  v1.1.0/
    cost-containment-rules.json  # Modified threshold value
    cost-containment-policy.json
```

When deploying v1.1.0, POST the updated rule definition. The rule ID remains stable; the condition field changes.

## Deployment to Environment

Rules and policies deploy via HTTP POST to the target Hexarch instance. No built-in promotion workflow exists.

**Deployment workflow**:
1. Validate JSON syntax in policy files.
2. POST rules to `/rules` endpoint in dependency order.
3. Collect returned `rule_id` values.
4. Update policy definitions with collected `rule_ids`.
5. POST policies to `/policies` endpoint.
6. Verify deployment by calling `/authorize` with test payloads.

**Example deployment script**:
```bash
#!/bin/bash
HEXARCH_URL="http://localhost:8000"

# Deploy rule
RULE_ID=$(curl -s -X POST $HEXARCH_URL/rules \
  -H "Authorization: Bearer $HEXARCH_API_TOKEN" \
  -d @cost-containment-rule.json | jq -r '.id')

# Deploy policy
curl -X POST $HEXARCH_URL/policies \
  -H "Authorization: Bearer $HEXARCH_API_TOKEN" \
  -d "{\"name\":\"cost_policy\",\"scope\":\"GLOBAL\",\"failure_mode\":\"FAIL_CLOSED\",\"rule_ids\":[\"$RULE_ID\"]}"
```

## Audit and Log Retention Considerations

Hexarch does not persist `/authorize` request/response logs by default. Authorization decisions are stateless.

**Audit pattern**:
1. Orchestrator logs `/authorize` requests and responses locally.
2. Include `decision`, `reason`, and `policies` fields in log output.
3. Forward logs to centralized logging infrastructure (e.g., Elasticsearch, Splunk).
4. Retention period matches organizational compliance requirements (30d, 90d, 1y).

**Example n8n logging node**:
```json
{
  "name": "Log Authorization Decision",
  "type": "n8n-nodes-base.function",
  "parameters": {
    "functionCode": "console.log(JSON.stringify({\n  timestamp: new Date().toISOString(),\n  decision: $json.decision,\n  reason: $json.reason,\n  policies: $json.policies\n}));\nreturn $input.all();"
  }
}
```

For structured audit trails, integrate Hexarch with external audit systems via API middleware that wraps `/authorize` calls.

## Policy Deprecation Process

To deprecate a policy:

1. **Identify dependent workflows**: Search orchestrator configurations for references to the policy name or associated rules.
2. **Create replacement policy**: Deploy new policy with updated rule set before removing old policy.
3. **Update workflows**: Migrate workflows to use new policy scope or rule conditions.
4. **Monitor deny rates**: Track authorization deny counts before and after migration to detect unintended enforcement changes.
5. **Delete policy**: After validation period (e.g., 7 days with zero references), DELETE policy via API.
6. **Archive rule definitions**: Move deprecated rule JSON files to `policies/deprecated/` folder with deprecation date.

**Example deprecation**:
```bash
# List policies to find ID
curl -X GET http://localhost:8000/policies \
  -H "Authorization: Bearer $HEXARCH_API_TOKEN"

# Delete policy by ID
curl -X DELETE http://localhost:8000/policies/{policy_id} \
  -H "Authorization: Bearer $HEXARCH_API_TOKEN"
```

**Retention**: Keep deprecated policy definitions in version control for audit and rollback scenarios. Do not delete from repository.

## Summary

- **Rule creation**: Define condition, POST to `/rules`, save rule ID.
- **Policy grouping**: Bind rules with shared scope and failure mode.
- **Versioning**: Track policy definitions in version-controlled JSON files with semantic versions.
- **Deployment**: POST rules and policies to target environment via API.
- **Audit**: Orchestrator logs `/authorize` responses; forward to centralized logging.
- **Deprecation**: Create replacement, migrate workflows, delete after validation period, archive definitions.

This lifecycle supports operational governance at scale.
