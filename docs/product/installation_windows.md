# Installation Guide - Windows

## Prerequisites

- Python 3.11 or later
- Node.js 18 or later
- Git

## Quick Install

```powershell
git clone https://github.com/GK0421/cogalpha-research-mvp.git
cd cogalpha-research-mvp
powershell -ExecutionPolicy Bypass -File scripts\install_studio.ps1
```

The installer will:
1. Check Python, Node, and Git
2. Create a `.venv` virtual environment
3. Install Python dependencies
4. Install and build frontend
5. Initialize workspace at `~/.cogalpha/`

## Manual Install

```powershell
# Create venv
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install Python deps
pip install -e ".[dev]"

# Install and build frontend
cd apps\web
npm install
npm run build
cd ..\..
```

## Start Studio

```powershell
scripts\start_studio.ps1
```

Browser opens at `http://127.0.0.1:8765`.

## Stop Studio

```powershell
scripts\stop_studio.ps1
```

## Reset

```powershell
# Clear cache only (safe)
scripts\reset_studio.ps1

# Clear everything including metadata
scripts\reset_studio.ps1 -IncludeMetadata -Force
```

## Uninstall

```powershell
# Remove venv and node_modules (keeps user data)
scripts\uninstall_studio.ps1

# Remove everything including user data
scripts\uninstall_studio.ps1 -IncludeUserData -Force
```

## Troubleshooting

- **Port 8765 in use**: Use `scripts\stop_studio.ps1` first, or edit port in `start_studio.ps1`
- **Python not found**: Ensure Python is in PATH
- **npm install fails**: Try `npm cache clean --force` then retry
