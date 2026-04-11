# Hexarch Guardrails Python SDK

Lightweight policy-driven API protection for developers and small teams.

[![PyPI version](https://badge.fury.io/py/hexarch-guardrails.svg)](https://pypi.org/project/hexarch-guardrails/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**[📘 Docs](./docs/)** | **[🚀 Interactive Demo](https://colab.research.google.com/github/no1rstack/hexarch-guardrails/blob/main/demos/hexarch_guardrails_demo.ipynb)** | **[💬 Discussions](https://github.com/no1rstack/hexarch-guardrails/discussions)** | **[🎯 Templates](./templates/)**

## Source-of-truth

This SDK is synced from the private monorepo (`no1rstack/Hexarch`) via an automated subtree publish workflow.

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

# ⚠️ Requires a running OPA server (local or remote)

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

### 3. Start OPA locally (if not already running)

```bash
docker run -p 8181:8181 openpolicyagent/opa:latest run --server
```

Then run your script as usual.

## Features

- ✅ **Zero-policy-language changes** - Auto-discovers `hexarch.yaml`; YAML + rule DSL, no code restructuring
- ✅ **Decorator-based** - Drop in `@guardian.check(policy_id)`
- ✅ **Policy-driven** - YAML-based rules, OPA-backed evaluation
- ✅ **Works with OPA** - Local or remote OPA server; requires OPA connectivity
- ✅ **Per-process rate limiting** - Built-in sliding-window limiter per instance
- ✅ **Pluggable** - Works with any API/SDK

## 🎉 Try It Now (Zero Install)

**[→ Interactive Demo on Google Colab](https://colab.research.google.com/github/no1rstack/hexarch-guardrails/blob/main/demos/hexarch_guardrails_demo.ipynb)**

See policy violations in action without installing anything. Click, run cells, and watch guardrails protect your code.

## Demos

- **Notebook demo**: [`demos/hexarch_guardrails_demo.ipynb`](./demos/hexarch_guardrails_demo.ipynb)
- **CLI-friendly first-run demo**: [`demos/first_run_guarded_call_demo.py`](./demos/first_run_guarded_call_demo.py)
- **OPA preflight + policy probe demo**: [`demos/opa_preflight_policy_probe.py`](./demos/opa_preflight_policy_probe.py)

## 🌟 Trusted By

> **Building something with Hexarch?** [Share your story](https://github.com/no1rstack/hexarch-guardrails/discussions) and we'll feature you here!

<details>
<summary><b>Early adopter signals</b></summary>

- Early users report catching runaway API loops and overspend during development.
- Adopted in initial RAG app prototypes and hackathon builds.
- Public testimonials are added only when externally attributable.

</details>

### Community Stats

- 🏗️ **Built for**: Students, solo developers, hackathon teams, startups
- 🎯 **Use cases**: AI API protection, budget control, rate limiting, safe deployments
- 📦 **Integrations**: FastAPI, Django, LangChain, Flask ([see templates](./templates/))
- 🚀 **Quick start**: Under 5 minutes from install to protected

### Ready-to-Use Templates

Get started instantly with our integration templates:

- **[FastAPI](./templates/fastapi/)** - API rate limiting and budget protection
- **[Django](./templates/django/)** - View decorators and Celery task protection
- **[LangChain](./templates/langchain/)** - LLM call protection and agent safeguards

Each template includes complete code, policy configs, and usage instructions.

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
- [Implementation Audit](./docs/IMPLEMENTATION_AUDIT.md)
- [Technical Source Documentation (Implementation-Bound)](./docs/TECHNICAL_SOURCE_DOCUMENTATION.md)
- [Claims Validation Matrix](./docs/CLAIMS_VALIDATION_MATRIX.md)
- [Public Technical Overview](./docs/PUBLIC_DOCUMENTATION.md)
- [PyPI Claims Validation Report](./docs/PYPI_CLAIMS_VALIDATION.md)
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

If `hexarch-ctl` resolves to the wrong Python interpreter on Windows, use:

```bash
python -m hexarch_cli policy list
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

### Quick demo onboarding (`/demo`)

For a hosted sandbox flow (for example, `https://hexarch.systems/demo`), use the built-in demo session bootstrap:

1. Run `hexarch-ctl init` to request a short-lived bootstrap token.
2. The browser opens `/demo?token=...` and exchanges that token via `POST /api/demo/exchange`.
3. The exchanged token is scoped to demo session routes only (`/demo/policies`, `/demo/evaluate`).

Demo route behavior:
- Bootstrap tokens are short-lived and one-time exchange.
- Session tokens are short-lived and sandbox-scoped.
- Destructive actions are denied in `/demo/evaluate`.
- Demo evaluation is non-persistent by design.

Key demo environment variables:

| Variable | Purpose | Default |
|---|---|---|
| `HEXARCH_DEMO_TOKEN_SECRET` | HMAC signing secret for demo tokens | generated fallback |
| `HEXARCH_DEMO_ISSUE_RPM` | Per-IP rate limit for `POST /api/demo/session` | `5` |
| `HEXARCH_DEMO_EXCHANGE_RPM` | Per-IP rate limit for `POST /api/demo/exchange` | `20` |
| `HEXARCH_DEMO_SESSION_RPM` | Per-session rate limit for demo route usage | `60` |
| `HEXARCH_DEMO_WEB_URL` | URL used by `hexarch-ctl init` for browser redirect | `https://hexarch.systems/demo` |

> The current `/demo` UI style is adapted from Bootstrap examples (MIT).

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

## n8n Integration Example

Technical walkthrough for pre-execution policy enforcement in n8n with an importable workflow and deterministic allow/deny routing:

- [ADDING_PRE_EXECUTION_POLICY_ENFORCEMENT_TO_N8N_IN_15_MINUTES.md](./n8n/ADDING_PRE_EXECUTION_POLICY_ENFORCEMENT_TO_N8N_IN_15_MINUTES.md)

## GitHub Actions Integration Example

Technical walkthrough for pre-execution policy enforcement in GitHub Actions with an importable workflow pattern and deterministic allow/deny routing:

- [ADDING_PRE_EXECUTION_POLICY_ENFORCEMENT_TO_GITHUB_ACTIONS_IN_15_MINUTES.md](./github-actions/ADDING_PRE_EXECUTION_POLICY_ENFORCEMENT_TO_GITHUB_ACTIONS_IN_15_MINUTES.md)

## Postman Integration Example

Technical walkthrough for pre-execution policy enforcement in Postman with an importable collection, local environment, and deterministic allow/deny authorization checks:

- [ADDING_PRE_EXECUTION_POLICY_ENFORCEMENT_TO_POSTMAN_IN_15_MINUTES.md](./postman/ADDING_PRE_EXECUTION_POLICY_ENFORCEMENT_TO_POSTMAN_IN_15_MINUTES.md)

## Flowise Integration Example

Technical walkthrough for pre-execution policy enforcement in Flowise Agentflow V2 using HTTP, Condition, and Direct Reply nodes with shared `$flow.state` for deterministic allow/deny routing:

- [ADDING_PRE_EXECUTION_POLICY_ENFORCEMENT_TO_FLOWISE_IN_15_MINUTES.md](./flowise/ADDING_PRE_EXECUTION_POLICY_ENFORCEMENT_TO_FLOWISE_IN_15_MINUTES.md)

## Langflow Integration Example

Technical walkthrough for pre-execution policy enforcement in Langflow using the native `API Request` component, reusable guard subflows, and an optional custom component starter for deterministic allow/deny routing:

- [ADDING_PRE_EXECUTION_POLICY_ENFORCEMENT_TO_LANGFLOW_IN_15_MINUTES.md](./langflow/ADDING_PRE_EXECUTION_POLICY_ENFORCEMENT_TO_LANGFLOW_IN_15_MINUTES.md)

## Pipedream Integration Example

Technical walkthrough for pre-execution policy enforcement in Pipedream using two Node.js code steps — `check_policy` (POST to `/authorize`) and `enforce` (`$.flow.exit()` on deny) — to gate any downstream step with a deterministic allow/deny decision:

- [ADDING_PRE_EXECUTION_POLICY_ENFORCEMENT_TO_PIPEDREAM_IN_15_MINUTES.md](./pipedream/ADDING_PRE_EXECUTION_POLICY_ENFORCEMENT_TO_PIPEDREAM_IN_15_MINUTES.md)

## Zapier Integration Example

Technical walkthrough for pre-execution policy enforcement in Zapier using a Code by Zapier step (`check_policy`) and a built-in Filter step to gate any downstream Zap action with a deterministic allow/deny decision:

- [ADDING_PRE_EXECUTION_POLICY_ENFORCEMENT_TO_ZAPIER_IN_15_MINUTES.md](./zapier/ADDING_PRE_EXECUTION_POLICY_ENFORCEMENT_TO_ZAPIER_IN_15_MINUTES.md)

## Node-RED Integration Example

Technical walkthrough for pre-execution policy enforcement in Node-RED with an importable flow and deterministic allow/deny routing:

- [ADDING_PRE_EXECUTION_POLICY_ENFORCEMENT_TO_NODE_RED_IN_15_MINUTES.md](./node-red/ADDING_PRE_EXECUTION_POLICY_ENFORCEMENT_TO_NODE_RED_IN_15_MINUTES.md)

## Node-RED End-to-End (Single User Milestone)

If you prefer an Apache-2.0 OSS orchestrator for guardrails testing (authorize → echo → log provider call), see:

- [NODE_RED_SINGLE_USER_MILESTONE.md](./NODE_RED_SINGLE_USER_MILESTONE.md)

## PyPI release checklist

Use this checklist before publishing a new package version:

1. **Confirm version metadata**
  - Update `version` in `pyproject.toml`.
  - Ensure `hexarch_guardrails/__init__.py` exports matching `__version__`.
2. **Run validation locally**
  - Run full test suite (`python -m pytest -q`).
  - Run any required smoke checks for `hexarch-ctl` and server mode.
3. **Build distribution artifacts**
  - Build wheel/sdist (`python -m build`).
4. **Validate artifacts**
  - Run Twine checks (`python -m twine check dist/*`).
5. **Publish**
  - Upload to PyPI with Twine.
6. **Post-publish verification**
  - Install from PyPI in a clean env and run a quick `Guardian` + `hexarch-ctl` smoke test.

## License

MIT © Noir Stack LLC

See LICENSE for full details.

## License
This project is licensed under the Business Source License 1.1 (BSL).  
See the LICENSE file for details.

