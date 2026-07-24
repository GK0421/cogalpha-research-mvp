# scripts/reset_studio.ps1
# CogAlpha Studio - Reset cache (metadata deletion requires explicit confirmation)

param(
    [switch]$IncludeMetadata,
    [switch]$Force
)

$ErrorActionPreference = "Stop"

Write-Host "[CogAlpha Studio] Reset..." -ForegroundColor Cyan

# Determine workspace
$home_ = $env:COGALPHA_HOME
if (-not $home_) {
    $home_ = Join-Path $env:USERPROFILE ".cogalpha"
}

if (-not (Test-Path $home_)) {
    Write-Host "Workspace not found at $home_" -ForegroundColor DarkYellow
    exit 0
}

# --- Clear caches (safe, no confirmation needed) ---
$cacheDir = Join-Path $home_ "cache"
if (Test-Path $cacheDir) {
    Write-Host "Clearing cache: $cacheDir" -ForegroundColor Yellow
    Remove-Item $cacheDir -Recurse -Force
    Write-Host "  Cache cleared." -ForegroundColor Green
} else {
    Write-Host "No cache directory found." -ForegroundColor DarkGray
}

# --- Clear logs ---
$logDir = Join-Path $home_ "logs"
if (Test-Path $logDir) {
    Write-Host "Clearing logs: $logDir" -ForegroundColor Yellow
    Remove-Item $logDir -Recurse -Force
    Write-Host "  Logs cleared." -ForegroundColor Green
}

# --- Metadata deletion requires explicit confirmation ---
if ($IncludeMetadata) {
    if (-not $Force) {
        Write-Host "`nWARNING: You are about to delete ALL project metadata, datasets, factors, and runs." -ForegroundColor Red
        Write-Host "This action CANNOT be undone." -ForegroundColor Red
        $confirm = Read-Host "`nType 'DELETE EVERYTHING' to confirm"
        if ($confirm -ne "DELETE EVERYTHING") {
            Write-Host "Confirmation not received. Aborting metadata deletion." -ForegroundColor Yellow
            exit 0
        }
    }

    $dbPath = Join-Path $home_ "cogalpha.db"
    if (Test-Path $dbPath) {
        Write-Host "Deleting database: $dbPath" -ForegroundColor Red
        Remove-Item $dbPath -Force
    }

    $runsDir = Join-Path $home_ "runs"
    if (Test-Path $runsDir) {
        Write-Host "Deleting runs: $runsDir" -ForegroundColor Red
        Remove-Item $runsDir -Recurse -Force
    }

    $reportsDir = Join-Path $home_ "reports"
    if (Test-Path $reportsDir) {
        Write-Host "Deleting reports: $reportsDir" -ForegroundColor Red
        Remove-Item $reportsDir -Recurse -Force
    }

    Write-Host "Metadata deleted." -ForegroundColor Green
}

Write-Host "`nReset complete." -ForegroundColor Cyan
