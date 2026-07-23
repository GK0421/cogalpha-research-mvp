# scripts/bootstrap.ps1 - Set up development environment
# Creates .venv, installs dependencies, runs doctor

$ErrorActionPreference = "Stop"

Write-Host "=== CogAlpha Research MVP - Bootstrap ===" -ForegroundColor Cyan

# Check Python version
$pythonVersion = python --version 2>&1
Write-Host "Python: $pythonVersion"

# Create virtual environment
if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .venv\Scripts\Activate.ps1

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip setuptools wheel

# Install package with dev dependencies
Write-Host "Installing package with dev dependencies..." -ForegroundColor Yellow
pip install -e ".[dev]"

# Run doctor
Write-Host "Running environment check..." -ForegroundColor Yellow
python -m cogalpha_mvp.cli doctor

Write-Host ""
Write-Host "=== Bootstrap Complete ===" -ForegroundColor Green
Write-Host "To activate the environment: .venv\Scripts\Activate.ps1"
