# Node-RED + Hexarch: Single-User Guardrails Testing

This is the simplest free/OSS local orchestration setup to validate guardrails.

## Milestone closure (individual usage)

Consider the **single-user use case closed** when the following pass on a clean machine (Windows + Docker Desktop is the reference target):

1. `hexarch-ctl node-red bootstrap --start-server --init-db --leave-running` succeeds and writes `node-red/.env.node-red`.
2. `hexarch-ctl node-red up` starts Node-RED and the flow is available.
3. `hexarch-ctl node-red verify` returns `Audit verify: ok=True` and a non-zero provider-call count.

Notes:
- If you omit `--database-url`, bootstrap uses an isolated per-run SQLite DB under `.run/` when `--init-db` is set.
- If you want deterministic ports, pass `--port` to bootstrap and ensure nothing else is listening there.

## 1) Start Hexarch API

From `hexarch-guardrails-py/`:

```powershell
$env:DATABASE_URL = "sqlite:///./hexarch.db"
$env:HEXARCH_API_TOKEN = "dev-token"

hexarch-ctl serve api --host 127.0.0.1 --port 8099 --init-db --bootstrap-allow --bootstrap-ttl-seconds 900
```

Optional (recommended): generate a dedicated API key for Node-RED and write `node-red/.env.node-red`:

```powershell
# One-shot: starts Hexarch with API key admin enabled, mints a key, then restarts locked-down.
# If you omit --database-url, it will use an isolated per-run SQLite DB under `.run/` when --init-db is set.
hexarch-ctl node-red bootstrap --start-server --host 127.0.0.1 --port 8099 --init-db --bootstrap-ttl-seconds 900
```

Quick verification (triggers the flow, then checks provider-call + audit chain):

```powershell
hexarch-ctl node-red verify
```

Alternative (env vars):

```powershell
$env:HEXARCH_BOOTSTRAP_ALLOW = "true"
$env:HEXARCH_BOOTSTRAP_TTL_SECONDS = "900"
hexarch-ctl serve api --host 127.0.0.1 --port 8099 --init-db
```

Create one bootstrap allow policy (otherwise `/authorize` denies by default):

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

## 2) Start Node-RED (Docker)

From `hexarch-guardrails-py/`:

```powershell
# Copy the example env file and set HEXARCH_TOKEN (recommended: API key)
Copy-Item .\node-red\.env.node-red.example .\node-red\.env.node-red

# Start Node-RED
hexarch-ctl node-red up
```

Open Node-RED:
- http://localhost:1880

## 3) Flow (auto-loaded)

The compose file bind-mounts `node-red/data` to `/data` and sets `FLOWS=flows.json`, so the flow is preloaded on startup.

Open Node-RED:
- http://localhost:1880

## 4) Run

Option A (no-click): trigger the flow via HTTP:

```powershell
Invoke-WebRequest -UseBasicParsing -Method POST http://localhost:1880/hexarch/run | Select-Object -ExpandProperty Content
```

Optional: export a dated evidence markdown file:

```powershell
hexarch-ctl node-red evidence
```

Option B (UI): click the **Run** inject node.

Flow behavior:
1) calls `POST /authorize`
2) if allowed, calls public `POST /echo`
3) logs a tamper-evident provider call event via `POST /events/provider-calls`

## 5) Verify

Provider call events:

```powershell
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8099/events/provider-calls -Headers @{ Authorization = "Bearer dev-token"; "X-Actor-Id" = "admin" } |
  Select-Object -ExpandProperty Content
```

Audit chain integrity:

```powershell
Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:8099/audit-logs/verify?chain_id=global" -Headers @{ Authorization = "Bearer dev-token"; "X-Actor-Id" = "admin" } |
  Select-Object -ExpandProperty Content
```

## Notes

- The flow assumes Node-RED is running in Docker and Hexarch runs on the host.
- On Windows/Mac Docker Desktop, `host.docker.internal` works.
- On Linux, you may need to replace `host.docker.internal` with the host gateway IP or run both services in one compose network.
