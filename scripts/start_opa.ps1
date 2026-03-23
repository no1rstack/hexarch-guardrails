param(
  [int]$Port = 8181,
  [string]$BindHost = "127.0.0.1",
  [int]$HealthTimeoutSeconds = 20,
  [switch]$Foreground
)

$ErrorActionPreference = "Stop"

function Resolve-OpaPath {
  $cmd = Get-Command opa -ErrorAction SilentlyContinue
  if ($cmd -and $cmd.Source) {
    return $cmd.Source
  }

  $wingetPath = Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Packages\open-policy-agent.opa_Microsoft.Winget.Source_8wekyb3d8bbwe\opa.exe"
  if (Test-Path $wingetPath) {
    return $wingetPath
  }

  $matches = Get-ChildItem (Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Packages") -Directory -Filter "*open-policy-agent.opa*" -ErrorAction SilentlyContinue |
    ForEach-Object {
      Join-Path $_.FullName "opa.exe"
    } |
    Where-Object { Test-Path $_ }

  if ($matches) {
    return $matches | Select-Object -First 1
  }

  return $null
}

$opaExe = Resolve-OpaPath
if (-not $opaExe) {
  throw "OPA executable not found. Install with: winget install --id open-policy-agent.opa -e"
}

$healthUrl = "http://$BindHost`:$Port/health"

try {
  $existing = Invoke-WebRequest -UseBasicParsing -Uri $healthUrl -TimeoutSec 2
  if ($existing.StatusCode -eq 200) {
    Write-Host "OPA already running at $healthUrl"
    return
  }
} catch {
  # OPA not up yet, continue startup path.
}

if ($Foreground) {
  Write-Host "Starting OPA in foreground at $healthUrl"
  & $opaExe run --server --addr "$BindHost`:$Port"
  exit $LASTEXITCODE
}

Write-Host "Starting OPA in background at $healthUrl"
$proc = Start-Process -FilePath $opaExe -ArgumentList @("run", "--server", "--addr", "$BindHost`:$Port") -PassThru

$deadline = (Get-Date).AddSeconds($HealthTimeoutSeconds)
$ok = $false
while ((Get-Date) -lt $deadline) {
  Start-Sleep -Milliseconds 250
  try {
    $resp = Invoke-WebRequest -UseBasicParsing -Uri $healthUrl -TimeoutSec 2
    if ($resp.StatusCode -eq 200) {
      $ok = $true
      break
    }
  } catch {
    # waiting for OPA startup
  }
}

if (-not $ok) {
  if ($proc -and -not $proc.HasExited) {
    Stop-Process -Id $proc.Id -Force
  }
  throw "OPA did not become healthy within $HealthTimeoutSeconds seconds."
}

$pidFile = Join-Path (Split-Path -Parent $PSScriptRoot) ".opa.pid"
Set-Content -Path $pidFile -Value "$($proc.Id)"

Write-Host "OPA is healthy at $healthUrl"
Write-Host "OPA PID: $($proc.Id) (saved to .opa.pid)"
