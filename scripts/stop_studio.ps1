# scripts/stop_studio.ps1
# CogAlpha Studio - Stop backend by PID (does not kill by process name)

param(
    [string]$Root = $PSScriptRoot | Split-Path -Parent
)

$ErrorActionPreference = "Stop"

Write-Host "[CogAlpha Studio] Stopping..." -ForegroundColor Cyan

$PidFile = Join-Path $env:LOCALAPPDATA "cogalpha-studio\studio.pid"

if (-not (Test-Path $PidFile)) {
    Write-Host "No PID file found. Studio may not be running." -ForegroundColor DarkYellow
    exit 0
}

$pidVal = (Get-Content $PidFile -Raw).Trim()

if (-not $pidVal -or $pidVal -notmatch '^\d+$') {
    Write-Host "Invalid PID file. Removing." -ForegroundColor DarkYellow
    Remove-Item $PidFile -Force
    exit 0
}

$proc = Get-Process -Id $pidVal -ErrorAction SilentlyContinue

if ($proc) {
    Write-Host "Stopping backend (PID $pidVal)..." -ForegroundColor Yellow
    Stop-Process -Id $pidVal -Force
    Start-Sleep -Seconds 1
    Write-Host "  Stopped." -ForegroundColor Green
} else {
    Write-Host "Process $pidVal not found (may have already stopped)." -ForegroundColor DarkGray
}

Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
Write-Host "Studio stopped." -ForegroundColor Cyan
