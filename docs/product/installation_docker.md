# Installation Guide - Docker

## Prerequisites

- Docker 20.10+
- Docker Compose 2.0+

## Quick Start

```bash
cd docker
docker compose up --build
```

- API: `http://127.0.0.1:8765`
- Web: `http://127.0.0.1:8080`

## Services

| Service | Port | Description |
|---------|------|-------------|
| api | 8765 | FastAPI backend (127.0.0.1 only) |
| web | 8080 | Nginx serving React frontend |

## Data Persistence

Workspace data is stored in a Docker volume (`cogalpha-workspace`).
This survives container restarts.

```bash
# View volumes
docker volume ls | grep cogalpha

# Remove volume (deletes all data)
docker compose down -v
```

## Health Check

```bash
curl http://127.0.0.1:8765/api/health
# {"status":"ok","version":"0.2.1"}
```

## Stop

```bash
docker compose down
```

## Building Individual Images

```bash
# API only
docker build -f docker/Dockerfile.api -t cogalpha-api .

# Web only
docker build -f docker/Dockerfile.web -t cogalpha-web .
```

## Security Notes

- Non-root user in containers
- Localhost-only port binding
- No API keys in images
- No real data in images
