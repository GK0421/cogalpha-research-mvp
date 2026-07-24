# scripts/install_studio.ps1
# CogAlpha Studio Windows Installer
# Checks: Python, Node, Git; Creates .venv; Installs deps; Builds frontend

param(
    [string]$Root = $PSScriptRoot | Split-Path -Parent
)

$ErrorActionPreference = "Stop"

Write-Host "[CogAlpha Studio] Installation starting..." -ForegroundColor Cyan

# --- Check prerequisites ---
Write-Host "`n[1/6] Checking prerequisites..." -ForegroundColor Yellow

$pythonOk = $false
try { $pythonVer = python --version 2>&1; if ($pythonVer -match "3\.(11|12|13)") { $pythonOk = $true; Write-Host "  Python: $pythonVer" -ForegroundColor Green } else { Write-Host "  Python: $pythonVer (need 3.11+)" -ForegroundColor Red } } catch { Write-Host "  Python: NOT FOUND" -ForegroundColor Red }

$nodeOk = $false
try { $nodeVer = node --version 2>&1; if ($nodeVer -match "v(1[8-9]|[2-9]\d)") { $nodeOk = $true; Write-Host "  Node: $nodeVer" -ForegroundColor Green } else { Write-Host "  Node: $nodeVer (need 18+)" -ForegroundColor Red } } catch { Write-Host "  Node: NOT FOUND" -ForegroundColor Red }

$gitOk = $false
try { $gitVer = git --version 2>&1; if ($LASTEXITCODE -eq 0) { $gitOk = $true; Write-Host "  Git: $gitVer" -ForegroundColor Green } } catch { Write-Host "  Git: NOT FOUND" -ForegroundColor Red }

if (-not ($pythonOk -and $nodeOk -and $gitOk)) {
    Write-Host "`nPrerequisites not met. Please install missing tools." -ForegroundColor Red
    exit 1
}

# --- Create virtual environment ---
Write-Host "`n[2/6] Creating Python virtual environment..." -ForegroundColor Yellow
$VenvPath = Join-Path $Root ".venv"
if (Test-Path $VenvPath) {
    Write-Host "  .venv already exists, skipping creation." -ForegroundColor DarkGray
} else {
    python -m venv $VenvPath
    Write-Host "  Created .venv" -ForegroundColor Green
}

$PipExe = Join-Path $VenvPath "Scripts\pip.exe"
$PythonExe = Join-Path $VenvPath "Scripts\python.exe"

# --- Install Python dependencies ---
Write-Host "`n[3/6] Installing Python dependencies..." -ForegroundColor Yellow
& $PipExe install --upgrade pip --quiet
& $PipExe install -e "$Root[dev]" --quiet 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "  Failed to install Python dependencies" -ForegroundColor Red
    exit 1
}
Write-Host "  Python dependencies installed" -ForegroundColor Green

# --- Install frontend dependencies ---
Write-Host "`n[4/6] Installing frontend dependencies..." -ForegroundColor Yellow
$WebDir = Join-Path $Root "apps\web"
Push-Location $WebDir
npm install --silent 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "  Failed to install frontend dependencies" -ForegroundColor Red
    Pop-Location
    exit 1
}
Write-Host "  Frontend dependencies installed" -ForegroundColor Green

# --- Build frontend ---
Write-Host "`n[5/6] Building frontend..." -ForegroundColor Yellow
npm run build 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "  Frontend build failed" -ForegroundColor Red
    Pop-Location
    exit 1
}
Write-Host "  Frontend built to dist/" -ForegroundColor Green
Pop-Location

# --- Initialize workspace ---
Write-Host "`n[6/6] Initializing workspace..." -ForegroundColor Yellow
& $PythonExe -c "from cogalpha_mvp.product.paths import WorkspaceManager; WorkspaceManager().initialize(); print('  Workspace initialized')" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "  Workspace initialization failed (non-fatal)" -ForegroundColor DarkYellow
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Installation complete!" -ForegroundColor Green
Write-Host "  Start with: scripts\start_studio.ps1" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
