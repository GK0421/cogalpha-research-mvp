# scripts/uninstall_studio.ps1
# CogAlpha Studio - Uninstall (does NOT delete user data unless --IncludeUserData)

param(
    [switch]$IncludeUserData,
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot | Split-Path -Parent

Write-Host "[CogAlpha Studio] Uninstall..." -ForegroundColor Cyan

# --- Stop running instance ---
$stopScript = Join-Path $Root "scripts\stop_studio.ps1"
if (Test-Path $stopScript) {
    & $stopScript 2>&1 | Out-Null
}

# --- Remove virtual environment ---
$venvPath = Join-Path $Root ".venv"
if (Test-Path $venvPath) {
    Write-Host "Removing .venv..." -ForegroundColor Yellow
    Remove-Item $venvPath -Recurse -Force
    Write-Host "  .venv removed." -ForegroundColor Green
}

# --- Remove node_modules ---
$nodeModules = Join-Path $Root "apps\web\node_modules"
if (Test-Path $nodeModules) {
    Write-Host "Removing node_modules..." -ForegroundColor Yellow
    Remove-Item $nodeModules -Recurse -Force
    Write-Host "  node_modules removed." -ForegroundColor Green
}

# --- Remove frontend dist ---
$distDir = Join-Path $Root "apps\web\dist"
if (Test-Path $distDir) {
    Write-Host "Removing frontend dist..." -ForegroundColor Yellow
    Remove-Item $distDir -Recurse -Force
    Write-Host "  dist removed." -ForegroundColor Green
}

# --- User data deletion (requires explicit flag) ---
if ($IncludeUserData) {
    $home_ = $env:COGALPHA_HOME
    if (-not $home_) {
        $home_ = Join-Path $env:USERPROFILE ".cogalpha"
    }

    if (Test-Path $home_) {
        if (-not $Force) {
            Write-Host "`nWARNING: About to delete ALL user data at $home_" -ForegroundColor Red
            Write-Host "This includes all projects, datasets, factors, runs, and reports." -ForegroundColor Red
            $confirm = Read-Host "`nType 'DELETE ALL DATA' to confirm"
            if ($confirm -ne "DELETE ALL DATA") {
                Write-Host "Confirmation not received. User data preserved." -ForegroundColor Yellow
                exit 0
            }
        }

        Write-Host "Deleting user data: $home_" -ForegroundColor Red
        Remove-Item $home_ -Recurse -Force
        Write-Host "  User data deleted." -ForegroundColor Green
    } else {
        Write-Host "No user data directory found." -ForegroundColor DarkGray
    }
} else {
    Write-Host "`nUser data preserved. Use -IncludeUserData to delete." -ForegroundColor DarkGray
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Uninstall complete!" -ForegroundColor Green
Write-Host "  (Git repository not affected)" -ForegroundColor DarkGray
Write-Host "========================================" -ForegroundColor Cyan
