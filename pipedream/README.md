# Pipedream demo assets

This folder contains assets for demonstrating pre-execution policy enforcement in Pipedream.

## Contents

- `ADDING_PRE_EXECUTION_POLICY_ENFORCEMENT_TO_PIPEDREAM_IN_15_MINUTES.md` — main walkthrough
- `snippets/check-policy-step.js` — Node.js code step: POST to Hexarch /authorize, return decision
- `snippets/enforce-step.js` — Node.js code step: $.flow.exit() on deny, 403 response to caller
