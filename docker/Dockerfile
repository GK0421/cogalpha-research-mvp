# Dockerfile for CogAlpha Studio v0.2.0
# Multi-stage build: Python backend + Node frontend

# ---- Stage 1: Build frontend ----
FROM node:20-slim AS frontend-builder
WORKDIR /app/web
COPY apps/web/package.json apps/web/package-lock.json* ./
RUN npm install --silent
COPY apps/web/ ./
RUN npm run build

# ---- Stage 2: Python backend ----
FROM python:3.11-slim AS backend

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e ".[dev]"

# Copy source code
COPY src/ ./src/
COPY apps/api/ ./apps/api/
COPY configs/ ./configs/
COPY prompts/ ./prompts/

# Copy built frontend
COPY --from=frontend-builder /app/web/dist ./apps/web/dist

# Environment
ENV COGALPHA_HOST=0.0.0.0
ENV COGALPHA_PORT=8765
ENV PYTHONPATH=/app
EXPOSE 8765

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8765/api/v1/health')" || exit 1

# Run the API server
CMD ["python", "-m", "apps.api.server"]
