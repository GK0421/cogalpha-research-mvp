# scripts/start_studio.ps1
# CogAlpha Studio - Start backend + frontend, open browser

param(
    [int]$Port = 8765,
    [string]$Host_ = "127.0.0.1",
    [switch]$NoBrowser,
    [string]$Workspace,
    [string]$LogLevel = "info"
)

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot | Split-Path -Parent

Write-Host "[CogAlpha Studio] Starting..." -ForegroundColor Cyan

# --- Check port availability ---
$inUse = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
if ($inUse) {
    $existingPid = $inUse.OwningProcess | Select-Object -First 1
    Write-Host "Port $Port is already in use by PID $existingPid" -ForegroundColor Red
    exit 1
}

# --- Check for existing instance ---
$PidFile = Join-Path $env:LOCALAPPDATA "cogalpha-studio\studio.pid"
if (Test-Path $PidFile) {
    $oldPid = Get-Content $PidFile -Raw
    $oldPid = $oldPid.Trim()
    $proc = Get-Process -Id $oldPid -ErrorAction SilentlyContinue
    if ($proc) {
        Write-Host "Studio is already running (PID $oldPid). Use stop_studio.ps1 first." -ForegroundColor Red
        exit 1
    }
}

# --- Find Python ---
$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"
if (Test-Path $VenvPython) {
    $PythonExe = $VenvPython
} else {
    $PythonExe = "python"
}

# --- Build workspace env ---
$envArgs = @()
if ($Workspace) {
    $env:COGALPHA_HOME = $Workspace
}

# --- Start backend ---
Write-Host "Starting backend on ${Host_}:${Port}..." -ForegroundColor Yellow

$backendArgs = @(
    "-m", "uvicorn",
    "apps.api.server:app",
    "--host", $Host_,
    "--port", $Port,
    "--log-level", $LogLevel
)

$backendProc = Start-Process -FilePath $PythonExe -ArgumentList $backendArgs -WorkingDirectory $Root -PassThru -WindowStyle Minimized
Write-Host "  Backend PID: $($backendProc.Id)" -ForegroundColor Green

# --- Save PID ---
$PidDir = Join-Path $env:LOCALAPPDATA "cogalpha-studio"
New-Item -ItemType Directory -Path $PidDir -Force | Out-Null
"$($backendProc.Id)" | Out-File -FilePath $PidFile -Encoding ascii

# --- Wait for health check ---
Write-Host "Waiting for health check..." -ForegroundColor Yellow
$healthy = $false
for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Seconds 1
    try {
        $response = Invoke-RestMethod -Uri "http://${Host_}:${Port}/api/health" -Method GET -TimeoutSec 2 -ErrorAction Stop
        if ($response.status -eq "ok") {
            $healthy = $true
            break
        }
    } catch {
        # Still starting
    }
}

if ($healthy) {
    Write-Host "  Health check passed!" -ForegroundColor Green
} else {
    Write-Host "  Health check timeout (backend may still be starting)" -ForegroundColor DarkYellow
}

# --- Open browser ---
$url = "http://${Host_}:${Port}"
if (-not $NoBrowser) {
    Write-Host "Opening browser: $url" -ForegroundColor Cyan
    Start-Process $url
} else {
    Write-Host "Browser skipped. URL: $url" -ForegroundColor DarkGray
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  CogAlpha Studio is running!" -ForegroundColor Green
Write-Host "  URL: $url" -ForegroundColor Cyan
Write-Host "  Stop with: scripts\stop_studio.ps1" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
