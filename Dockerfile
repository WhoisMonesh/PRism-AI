# PRism-AI Dockerfile
# Multi-stage build: frontend-builder -> python-builder -> runtime

# ─── Frontend build stage ──────────────────────────────────────────────────
FROM node:20-slim AS frontend-builder
WORKDIR /build/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# ─── Python build stage ────────────────────────────────────────────────────
FROM python:3.11-slim AS builder
WORKDIR /build
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl git \
    && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml ./
RUN pip install --upgrade pip && \
    pip install --no-cache-dir ".[all]"

# ─── Runtime stage ───────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime
WORKDIR /app

# Security: non-root user
RUN groupadd -r prism && useradd -r -g prism -d /app prism

# Copy installed packages
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application source
COPY src/ ./src/
# Copy built frontend
COPY --from=frontend-builder /build/frontend/dist ./frontend/dist

# Create data directory
RUN mkdir -p /app/data /app/secrets && chown -R prism:prism /app

USER prism
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')"

CMD ["uvicorn", "src.api.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "2", \
     "--log-level", "info", \
     "--access-log"]
