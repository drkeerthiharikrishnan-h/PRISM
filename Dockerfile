# PRISM — Persona-Driven Research Intelligence System
# Multi-stage build using uv for fast, reproducible installs

FROM python:3.11-slim AS base

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

# Copy dependency files first — Docker caches this layer
# so re-installs only happen when pyproject.toml/uv.lock change
COPY pyproject.toml uv.lock ./

# Install production dependencies only (no dev/test packages)
RUN uv sync --no-dev --frozen

# Copy application code
COPY main.py orchestrator.py entity_resolver.py users.py ./
COPY connectors/ ./connectors/
COPY personas/   ./personas/
COPY frontend/   ./frontend/
COPY cache/      ./cache/

# Create cache directory (in case cache/ is empty)
RUN mkdir -p cache

EXPOSE 8000

# Run with uvicorn — host 0.0.0.0 so Docker port mapping works
CMD [".venv/bin/uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
