param(
  [string]$OpaUrl = "http://127.0.0.1:8181"
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Write-Host "Checking OPA health at $OpaUrl/health"
try {
  $health = Invoke-WebRequest -UseBasicParsing -Uri "$OpaUrl/health" -TimeoutSec 5
  if ($health.StatusCode -ne 200) {
    throw "Unexpected health status: $($health.StatusCode)"
  }
} catch {
  throw "OPA is not reachable at $OpaUrl. Start it first with scripts/start_opa.ps1"
}

$pythonCode = @"
import requests
from hexarch_guardrails.templates import DEFAULT_POLICY_TEMPLATES

opa_url = r"$OpaUrl".rstrip("/")

for name, content in DEFAULT_POLICY_TEMPLATES.items():
    resp = requests.put(
        f"{opa_url}/v1/policies/{name}",
        data=content,
        headers={"Content-Type": "text/plain"},
        timeout=10,
    )
    if resp.status_code >= 400:
        raise SystemExit(f"Failed to publish {name}: {resp.status_code} {resp.text}")
    print(f"published {name}")

print("all default policies published")
"@

python -c $pythonCode
if ($LASTEXITCODE -ne 0) {
  throw "Failed to seed OPA policies."
}

Write-Host "OPA policies seeded successfully."
