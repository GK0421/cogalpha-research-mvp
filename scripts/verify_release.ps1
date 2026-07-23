# scripts/verify_release.ps1 - Pre-release verification
$ErrorActionPreference = "Stop"

Write-Host "=== CogAlpha Research MVP - Release Verification ===" -ForegroundColor Cyan

# Check Git status
Write-Host "`n--- Git Status ---" -ForegroundColor Yellow
gitStatus = git status --short
if ($gitStatus) {
    Write-Host "WARNING: Working directory is not clean:" -ForegroundColor Red
    Write-Host $gitStatus
}

# Check version consistency
Write-Host "`n--- Version Check ---" -ForegroundColor Yellow
$versionFile = Get-Content VERSION -Raw
$versionFile = $versionFile.Trim()
Write-Host "VERSION file: $versionFile"

# Check for secrets
Write-Host "`n--- Secret Scan ---" -ForegroundColor Yellow
$secretPatterns = @("sk-", "api_key", "apikey", "token", "password", "secret", "authorization", "bearer")
$foundSecrets = $false
Get-ChildItem -Recurse -Include *.py,*.yaml,*.yml,*.json,*.md,*.txt -Exclude .git |
    Where-Object { $_.FullName -notmatch '\.venv|__pycache__|\.git' } |
    ForEach-Object {
        $content = Get-Content $_.FullName -Raw -ErrorAction SilentlyContinue
        if ($content) {
            foreach ($pattern in $secretPatterns) {
                if ($content -match "(?i)$pattern\s*[=:]\s*['""]?[a-zA-Z0-9]{10,}") {
                    if ($_.Name -ne ".env.example" -and $_.Name -ne "SECURITY.md") {
                        Write-Host "POTENTIAL SECRET in $($_.FullName)" -ForegroundColor Red
                        $foundSecrets = $true
                    }
                }
            }
        }
    }
if (-not $foundSecrets) {
    Write-Host "No secrets found." -ForegroundColor Green
}

# Check required files
Write-Host "`n--- Required Files ---" -ForegroundColor Yellow
$requiredFiles = @("LICENSE", "NOTICE", "README.md", "VERSION", "pyproject.toml", "CHANGELOG.md", "SECURITY.md", ".gitignore")
foreach ($f in $requiredFiles) {
    if (Test-Path $f) {
        Write-Host "  OK: $f" -ForegroundColor Green
    } else {
        Write-Host "  MISSING: $f" -ForegroundColor Red
    }
}

# Run tests
Write-Host "`n--- Running Tests ---" -ForegroundColor Yellow
& scripts\run_tests.ps1

Write-Host "`n=== Verification Complete ===" -ForegroundColor Cyan
