param(
  [string]$DatabaseUrl = "sqlite:///./hexarch.db",
  [int]$ApiPort = 8900,
  [string]$ApiHost = "127.0.0.1",
  [int]$OpaPort = 8181,
  [string]$OpaHost = "127.0.0.1",
  [switch]$SkipMigrations,
  [switch]$SkipOpa,
  [switch]$SkipSeed
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

# API environment defaults for local dev
$env:DATABASE_URL = $DatabaseUrl
$env:HEXARCH_API_ALLOW_ANON = "true"
$env:HEXARCH_BOOTSTRAP_ALLOW = "true"
$env:HEXARCH_API_DOCS = "true"

Write-Host "Using DATABASE_URL=$env:DATABASE_URL"
Write-Host "API anon/docs/bootstrap are enabled for local dev"

if (-not $SkipMigrations) {
  Write-Host "Applying Alembic migrations..."
  python -m alembic upgrade head
  if ($LASTEXITCODE -ne 0) {
    throw "Alembic migration failed."
  }
}

$opaUrl = "http://$OpaHost`:$OpaPort"
if (-not $SkipOpa) {
  Write-Host "Starting OPA..."
  & (Join-Path $PSScriptRoot "start_opa.ps1") -BindHost $OpaHost -Port $OpaPort
}

if (-not $SkipSeed) {
  Write-Host "Seeding default OPA policies..."
  & (Join-Path $PSScriptRoot "seed_opa_policies.ps1") -OpaUrl $opaUrl
}

$apiUrl = "http://$ApiHost`:$ApiPort"
Write-Host "Starting API at $apiUrl ..."

$proc = Start-Process -FilePath "python" -ArgumentList @(
  "-m", "uvicorn",
  "hexarch_cli.server.app:app",
  "--reload",
  "--host", $ApiHost,
  "--port", $ApiPort
) -PassThru

$deadline = (Get-Date).AddSeconds(25)
$healthy = $false
while ((Get-Date) -lt $deadline) {
  Start-Sleep -Milliseconds 300
  try {
    $resp = Invoke-WebRequest -UseBasicParsing -Uri "$apiUrl/health" -TimeoutSec 3
    if ($resp.StatusCode -eq 200) {
      $healthy = $true
      break
    }
  } catch {
    # wait for API startup
  }
}

if (-not $healthy) {
  if ($proc -and -not $proc.HasExited) {
    Stop-Process -Id $proc.Id -Force
  }
  throw "API did not become healthy at $apiUrl/health"
}

$apiPidFile = Join-Path $root ".hexarch_api.pid"
Set-Content -Path $apiPidFile -Value "$($proc.Id)"

Write-Host ""
Write-Host "Local dev stack is up ✅"
Write-Host "OPA:  $opaUrl/health"
Write-Host "API:  $apiUrl/health"
Write-Host "Docs: $apiUrl/docs"
Write-Host "API PID: $($proc.Id) (saved to .hexarch_api.pid)"
