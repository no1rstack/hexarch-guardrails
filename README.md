# Hexarch Guardrails Python SDK

Lightweight policy-driven API protection for students, solo developers, and hackathons.

## Installation

```bash
pip install hexarch-guardrails
```

## Quick Start

### 1. Create a policy file (`hexarch.yaml`)

```yaml
policies:
  - id: "api_budget"
    description: "Protect against overspending"
    rules:
      - resource: "openai"
        monthly_budget: 10
        action: "warn_at_80%"

  - id: "rate_limit"
    description: "Prevent API abuse"
    rules:
      - resource: "*"
        requests_per_minute: 100
        action: "block"

  - id: "safe_delete"
    description: "Require confirmation for destructive ops"
    rules:
      - operation: "delete"
        action: "require_confirmation"
```

### 2. Use in your code

```python
from hexarch_guardrails import Guardian

# Initialize (auto-discovers hexarch.yaml)
guardian = Guardian()

# Protect API calls
@guardian.check("api_budget")
def call_openai(prompt):
    import openai
    return openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )

# Use it
response = call_openai("Hello AI!")
```

## Features

- ✅ **Zero-config** - Auto-discovers `hexarch.yaml`
- ✅ **Decorator-based** - Drop in `@guardian.check(policy_id)`
- ✅ **Policy-driven** - YAML-based rules, no code changes
- ✅ **Local-first** - Works offline or with local OPA
- ✅ **Pluggable** - Works with any API/SDK

## Examples

### Budget Protection (OpenAI)

```python
@guardian.check("api_budget")
def expensive_operation():
    # This call is protected by budget limits
    return openai.ChatCompletion.create(model="gpt-4", ...)
```

### Rate Limiting

```python
@guardian.check("rate_limit")
def send_discord_message(msg):
    return client.send(msg)
```

### Safe File Operations

```python
@guardian.check("safe_delete")
def delete_file(path):
    os.remove(path)
```

## Documentation

- [Policy Authoring Guide](./docs/POLICY_GUIDE.md)
- [API Reference](./docs/API_REFERENCE.md)
- [Examples](./examples/)

## Admin CLI (v0.3.0+)

Hexarch includes a command-line interface for managing policies and monitoring decisions:

### Installation

```bash
# Install with CLI extras
pip install hexarch-guardrails[cli]
```

### Quick Start

```bash
# List all policies
hexarch-ctl policy list

# Export a policy
hexarch-ctl policy export ai_governance --format rego

# Validate policy syntax
hexarch-ctl policy validate ./policy.rego

# Compare policy versions
hexarch-ctl policy diff ai_governance
```

### Available Commands

**Policy Management**:
- `hexarch-ctl policy list` - List all OPA policies
- `hexarch-ctl policy export` - Export policy to file or stdout
- `hexarch-ctl policy validate` - Validate OPA policy syntax
- `hexarch-ctl policy diff` - Compare policy versions

**Upcoming** (Phase 3-4):
- Decision querying and analysis
- Metrics and performance monitoring
- Configuration management

For detailed CLI documentation, see [POLICY_COMMANDS_GUIDE.md](./POLICY_COMMANDS_GUIDE.md)

## REST API Server (Phase 3)

Hexarch includes a hardened FastAPI server intended to back a UI/dev workflow.

### Install server extras

```bash
pip install "hexarch-guardrails[server]"
```

### Run locally (recommended)

```bash
hexarch-ctl serve api --host 127.0.0.1 --port 8099 --init-db --api-token dev-token
```

Notes:
- `/health` is public; most endpoints require a bearer token.
- API key management endpoints (`/api-keys`) are disabled by default and can be enabled explicitly with `HEXARCH_API_KEY_ADMIN_ENABLED=true`.

## Credibility: OpenAPI fuzz scan (Schemathesis)

This repo includes a reproducible harness that starts the local FastAPI server with docs enabled and runs a Schemathesis scan against `/openapi.json`.

- Installs: `pip install -e ".[server,credibility]"`
- Runs (Windows): `./scripts/run_openapi_credibility_scan.ps1 -MaxExamples 25`
- Output: `evidence/credibility/openapi-schemathesis/<timestamp>/`

The scan is configured with a conservative credibility check (`not_a_server_error`) to demonstrate resilience under generated inputs (no 5xx), without requiring that every auth error path is explicitly modeled in the OpenAPI spec.

## Credibility: OWASP ZAP baseline scan (Docker)

This repo also includes an OWASP ZAP baseline scan harness (passive scan + spider) that produces HTML/JSON/XML/Markdown reports.

- Runs (Windows): `./scripts/run_zap_baseline_credibility_scan.ps1 -Mins 1 -MaxWaitMins 5`
- Output: `evidence/credibility/zap-baseline/<timestamp>/`

Notes:
- By default it keeps auth enabled (hardened posture) and does not fail the command on warnings; it always writes the reports.
- For deeper crawling you can run with `-AllowAnon` (this changes server posture for the scan).
- To propagate ZAP exit codes (WARN/FAIL), pass `-Strict`.

## Credibility: Policy correctness evals (golden cases)

Golden-case evaluation that exercises the decision engine via `POST /authorize` and writes a dated report.

- Cases file: `evals/policy_cases.json` (edit/extend this as you like)
- Runs (Windows): `./scripts/run_policy_credibility_evals.ps1`
- Output: `evidence/credibility/policy-evals/<timestamp>/` (`report.md`, `results.json`, `server.log`)

### Smoke test (starts server, hits `/health`, stops)

PowerShell:

```powershell
./scripts/smoke_api.ps1 -Port 8099
```

Bash:

```bash
./scripts/smoke_api.sh
```

## n8n End-to-End (Single User Milestone)

For a complete local workflow that (1) calls `/authorize`, (2) calls a provider (Ollama), and (3) logs a tamper-evident provider-call event via `/events/provider-calls`, see:

- [N8N_SINGLE_USER_MILESTONE.md](./N8N_SINGLE_USER_MILESTONE.md)

## Node-RED End-to-End (Single User Milestone)

If you prefer an Apache-2.0 OSS orchestrator for guardrails testing (authorize → echo → log provider call), see:

- [NODE_RED_SINGLE_USER_MILESTONE.md](./NODE_RED_SINGLE_USER_MILESTONE.md)

## License

MIT © Noir Stack LLC

See LICENSE for full details.
