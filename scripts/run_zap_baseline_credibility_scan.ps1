Param(
  [int]$Mins = 1,
  [int]$MaxWaitMins = 5,
  [switch]$AllowAnon,
  [switch]$Strict
)

$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

if (-not (Test-Path -Path ".\.venv\Scripts\python.exe")) {
  Write-Error "Missing .venv. Create it with: python -m venv .venv; .\.venv\Scripts\pip install -e '.[server,credibility]'"
}

# Quick docker sanity check
try {
  docker version | Out-Null
} catch {
  Write-Error "Docker not available. Install Docker Desktop and ensure 'docker' works in this terminal."
}

$env:HEXARCH_ZAP_MINS = "$Mins"
$env:HEXARCH_ZAP_MAX_WAIT_MINS = "$MaxWaitMins"
$env:HEXARCH_ZAP_ALLOW_ANON = if ($AllowAnon) { 'true' } else { 'false' }
$env:HEXARCH_ZAP_STRICT = if ($Strict) { 'true' } else { 'false' }

& .\.venv\Scripts\python.exe .\scripts\run_zap_baseline_credibility_scan.py
exit $LASTEXITCODE
