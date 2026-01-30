Param(
  [int]$MaxExamples = 25
)

$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

if (-not (Test-Path -Path ".\.venv\Scripts\python.exe")) {
  Write-Error "Missing .venv. Create it with: python -m venv .venv; .\.venv\Scripts\pip install -e '.[server,credibility]'"
}

$env:HEXARCH_CREDIBILITY_MAX_EXAMPLES = "$MaxExamples"

& .\.venv\Scripts\python.exe .\scripts\run_openapi_credibility_scan.py
exit $LASTEXITCODE
