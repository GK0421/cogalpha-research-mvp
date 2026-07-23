# scripts/run_demo.ps1 - Run the full demo pipeline
$ErrorActionPreference = "Stop"

Write-Host "=== CogAlpha Research MVP - Demo Run ===" -ForegroundColor Cyan

# Activate virtual environment if exists
if (Test-Path ".venv\Scripts\Activate.ps1") {
    & .venv\Scripts\Activate.ps1
}

# Generate synthetic data and run full pipeline
Write-Host "Running demo with synthetic data..." -ForegroundColor Yellow
python -m cogalpha_mvp.cli demo --output-dir results --log-level INFO

if ($LASTEXITCODE -ne 0) {
    Write-Host "Demo failed with exit code $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "=== Demo Complete ===" -ForegroundColor Green
Write-Host "Check results/ for the report."
