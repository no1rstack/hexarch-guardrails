# Hexarch Guardrails - Policy Authoring Guide

## Policy File

Create a `hexarch.yaml` file in your project root:

```yaml
policies:
  - id: "api_budget"
    description: "Protect against overspending"
    rules:
      - resource: "openai"
        monthly_budget: 10
        action: "warn_at_80%"
```

`monthly_budget` is interpreted in USD unless otherwise configured.

## Common Fields

- `id`: Unique policy identifier
- `description`: Human-readable summary
- `rules`: One or more enforcement rules
- `resource`: Target service or operation
- `action`: Enforcement behavior (`warn_at_*`, `block`, `require_confirmation`)

## Quick Notes

- Policies are loaded from your YAML file; they are not hard-coded into the SDK.
- OPA must be reachable for policy evaluation.
- Use `guardian.list_policies()` to verify what loaded from your file.
