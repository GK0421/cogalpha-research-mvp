# Troubleshooting

## Common Issues

### Port 8765 already in use

```powershell
# Check what's using the port
Get-NetTCPConnection -LocalPort 8765

# Stop Studio
scripts\stop_studio.ps1

# Or use a different port
scripts\start_studio.ps1 -Port 8766
```

### Python not found

Ensure Python 3.11+ is installed and in PATH:
```powershell
python --version
# Should show 3.11.x or higher
```

### Frontend build fails

```powershell
cd apps\web
rm -rf node_modules package-lock.json
npm install
npm run build
```

### Database locked

If SQLite database is locked:
```powershell
scripts\stop_studio.ps1
scripts\reset_studio.ps1  # clears cache only
scripts\start_studio.ps1
```

### Health check timeout

Backend may take 10-30 seconds to start. Check:
```powershell
python -m cogalpha_mvp.cli studio-status
```

### Docker build fails

```bash
# Clean Docker cache
docker system prune -a

# Rebuild without cache
docker compose build --no-cache
```

### Coverage check fails

```powershell
# Run tests with coverage
python -m pytest --cov=src/cogalpha_mvp --cov-fail-under=85 -m "not slow"
```

### mypy errors

```powershell
mypy src apps/api
```

### ruff format issues

```powershell
ruff format src tests apps
ruff check --fix src tests apps
```

## Getting Help

1. Check [FAQ](#) (coming soon)
2. Run `python -m cogalpha_mvp.cli doctor` for diagnostics
3. Check logs at `~/.cogalpha/logs/`
4. Open an issue on GitHub

## Reset Everything

```powershell
scripts\stop_studio.ps1
scripts\reset_studio.ps1 -IncludeMetadata -Force
scripts\start_studio.ps1
```
