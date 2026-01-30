Param(
  [string]$CasesPath = "",
  [int]$BootstrapTtlSeconds = 600
)

$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

if (-not (Test-Path -Path ".\.venv\Scripts\python.exe")) {
  Write-Error "Missing .venv. Create it with: python -m venv .venv; .\.venv\Scripts\pip install -e '.[server,credibility]'"
}

if ($CasesPath -ne "") {
  $env:HEXARCH_POLICY_EVAL_CASES = $CasesPath
}

$env:HEXARCH_BOOTSTRAP_TTL_SECONDS = "$BootstrapTtlSeconds"

& .\.venv\Scripts\python.exe .\scripts\run_policy_credibility_evals.py
exit $LASTEXITCODE
