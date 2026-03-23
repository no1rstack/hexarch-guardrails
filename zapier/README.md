# Zapier Integration

Pre-execution policy enforcement for Zapier Zaps using Hexarch Guardrails.

## Files

| File | Purpose |
|---|---|
| [ADDING_PRE_EXECUTION_POLICY_ENFORCEMENT_TO_ZAPIER_IN_15_MINUTES.md](ADDING_PRE_EXECUTION_POLICY_ENFORCEMENT_TO_ZAPIER_IN_15_MINUTES.md) | Step-by-step guide: creating the rule, attaching the policy, building the Code + Filter step architecture in a Zap |
| [snippets/check-policy-step.js](snippets/check-policy-step.js) | Code by Zapier snippet: calls `/authorize`, returns `allowed`, `decision`, `reason` fields for the downstream Filter step |

## Pattern

```
Trigger (Webhooks / Schedule / App event)
  └─ check_policy  (Code by Zapier — POST /authorize, returns allowed field)
       └─ Filter   (Zapier built-in — only continue if allowed is true)
            └─ invoke_provider  (downstream action — skipped on deny)
```

All deny decisions appear in Zap History as "Filtered out" runs. No downstream actions are called.

For richer routing (Slack notification on deny, logging to a sheet), replace the Filter step with a Paths step.
