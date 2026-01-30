param(
  [int]$Port = 8099,
  [string]$BindHost = "127.0.0.1",
  [string]$DatabaseUrl = "sqlite:///./.smoke_hexarch.db",
  [string]$ApiToken = "dev-token",
  [int]$TimeoutSeconds = 15
)

$ErrorActionPreference = "Stop"

$env:DATABASE_URL = $DatabaseUrl
$env:HEXARCH_API_TOKEN = $ApiToken

# Keep defaults: auth required, docs disabled, rate limit enabled.

Write-Host "Starting API on http://$BindHost`:$Port ..."

$proc = Start-Process -FilePath "python" -ArgumentList @(
  "-m", "uvicorn",
  "hexarch_cli.server.app:app",
  "--host", $BindHost,
  "--port", $Port,
  "--log-level", "warning"
) -PassThru -NoNewWindow

try {
  $resp = $null
  $deadline = (Get-Date).AddSeconds($TimeoutSeconds)

  while ((Get-Date) -lt $deadline) {
    Start-Sleep -Milliseconds 250
    try {
      $resp = Invoke-WebRequest -UseBasicParsing "http://$BindHost`:$Port/health" -TimeoutSec 2
      if ($resp.StatusCode -eq 200) { break }
    } catch {
      # keep waiting
    }
  }

  if (-not $resp -or $resp.StatusCode -ne 200) {
    throw "Health check failed: API did not respond within ${TimeoutSeconds}s"
  }

  $body = $resp.Content | ConvertFrom-Json
  if ($body.status -ne "ok") {
    throw "Unexpected health response: $($resp.Content)"
  }

  Write-Host "OK: /health -> $($resp.Content)"
  exit 0
}
finally {
  if ($proc -and -not $proc.HasExited) {
    Stop-Process -Id $proc.Id -Force
  }
}
