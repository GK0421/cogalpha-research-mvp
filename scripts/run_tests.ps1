# scripts/run_tests.ps1 - Run all tests and quality checks
$ErrorActionPreference = "Stop"

Write-Host "=== CogAlpha Research MVP - Test Suite ===" -ForegroundColor Cyan

# Activate virtual environment if exists
if (Test-Path ".venv\Scripts\Activate.ps1") {
    & .venv\Scripts\Activate.ps1
}

$failed = $false

# Ruff check
Write-Host "`n--- Ruff Check ---" -ForegroundColor Yellow
ruff check src tests
if ($LASTEXITCODE -ne 0) { $failed = $true }

# Ruff format check
Write-Host "`n--- Ruff Format Check ---" -ForegroundColor Yellow
ruff format --check src tests
if ($LASTEXITCODE -ne 0) { $failed = $true }

# Mypy
Write-Host "`n--- Mypy ---" -ForegroundColor Yellow
mypy src
if ($LASTEXITCODE -ne 0) { $failed = $true }

# Pytest with coverage
Write-Host "`n--- Pytest ---" -ForegroundColor Yellow
pytest --cov=src/cogalpha_mvp --cov-report=term-missing --cov-report=html
if ($LASTEXITCODE -ne 0) { $failed = $true }

if ($failed) {
    Write-Host "`n=== TESTS FAILED ===" -ForegroundColor Red
    exit 1
} else {
    Write-Host "`n=== ALL TESTS PASSED ===" -ForegroundColor Green
    exit 0
}
