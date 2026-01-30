# n8n + Hexarch: Single-User End-to-End Milestone

Goal: prove an individual can run a local control-plane that:
1) authorizes an external call, 2) performs the call, 3) logs a tamper-evident event.

This milestone uses:
- Hexarch Guardrails API (this repo)
- n8n (Docker)
- Ollama (optional, local model server)
- Or the built-in public `/echo` endpoint (no Ollama required)

## 1) Start Hexarch API

From `hexarch-guardrails-py/`:

```powershell
# Windows PowerShell
$env:DATABASE_URL = "sqlite:///./hexarch.db"
$env:HEXARCH_BOOTSTRAP_ALLOW = "true"
$env:HEXARCH_API_TOKEN = "dev-token"

# Optional (only if you want to manage API keys):
# $env:HEXARCH_API_KEY_ADMIN_ENABLED = "true"

hexarch-ctl serve api --host 127.0.0.1 --port 8099 --init-db
```

Sanity check:

```powershell
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8099/health | Select-Object -ExpandProperty Content
```

## 2) Bootstrap one allow policy

Without at least one policy, `/authorize` denies by default.

```powershell
$headers = @{ Authorization = "Bearer dev-token"; "X-Actor-Id" = "admin" }
$body = @{
  name = "bootstrap-allow-all"
  description = "Allow all for single-user milestone"
  enabled = $true
  scope = "GLOBAL"
  scope_value = $null
  failure_mode = "FAIL_CLOSED"
  rule_ids = @()
} | ConvertTo-Json

Invoke-WebRequest -UseBasicParsing -Method POST http://127.0.0.1:8099/policies -Headers $headers -ContentType "application/json" -Body $body |
  Select-Object -ExpandProperty Content
```

## 3) Start n8n (Docker)

From `hexarch-guardrails-py/`:

```powershell
docker compose -f .\n8n\docker-compose.n8n.yml up
```

Open n8n:
- http://localhost:5678

## 4) Import the workflow

In n8n:
- Workflows → Import from File

Pick one:
- No Ollama required: `n8n/workflows/hexarch-single-user-echo.json`
- With Ollama: `n8n/workflows/hexarch-single-user-ollama.json`

Both workflows do:
1) `POST /authorize`
2) If allowed → call a provider (either Ollama or Hexarch `/echo`)
3) `POST /events/provider-calls` (writes tamper-evident audit event)

### Configure variables

The workflow uses a `Set Vars` node. For Windows Docker Desktop:
- `hexarchBaseUrl`: `http://host.docker.internal:8099`
- `hexarchToken`: `dev-token`

If you have Ollama running locally:
- `ollamaUrl`: `http://host.docker.internal:11434/api/generate`
- `model`: e.g. `llama3`

If you do NOT have Ollama running, use the echo workflow variant.

## 5) Verify results

After running the workflow, confirm you have provider-call events:

```powershell
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8099/events/provider-calls -Headers @{ Authorization = "Bearer dev-token"; "X-Actor-Id" = "admin" } |
  Select-Object -ExpandProperty Content
```

And confirm the audit chain verifies:

```powershell
Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:8099/audit-logs/verify?chain_id=global" -Headers @{ Authorization = "Bearer dev-token"; "X-Actor-Id" = "admin" } |
  Select-Object -ExpandProperty Content
```

## Notes

- This setup governs only traffic that your workflow/routes send through Hexarch.
- For Linux Docker (no `host.docker.internal` by default), either:
  - run Hexarch in the same Docker network, or
  - use the host gateway IP.
