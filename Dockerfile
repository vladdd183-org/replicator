# Stage 1: Build
FROM python:3.13-slim AS builder

WORKDIR /app

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy dependency files first for better caching
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev --no-install-project

# Copy application code
COPY src ./src
COPY piccolo_conf.py ./

# Install the project itself
RUN uv sync --frozen --no-dev


# Stage 2: Runtime
FROM python:3.13-slim AS runtime

WORKDIR /app

# Create non-root user for security
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid 1000 --shell /bin/bash appuser

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY --from=builder /app/src ./src
COPY --from=builder /app/piccolo_conf.py ./

# Set PATH to use virtual environment
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app"
ENV PYTHONUNBUFFERED=1

# Create directory for database (development)
RUN mkdir -p /app/data && chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/docs || exit 1

# Start application
CMD ["uvicorn", "src.App:app", "--host", "0.0.0.0", "--port", "8000"]



