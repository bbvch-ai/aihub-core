# Build stage
FROM python:3.13-slim AS builder
ARG VERSION

COPY --from=ghcr.io/astral-sh/uv:0.10.4 /uv /uvx /bin/

ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy workspace config + relevant packages.
# sysadmin-api depends on swiss-ai-hub-core and swiss-ai-hub-api as workspace deps,
# so all three must be present.
COPY pyproject.toml uv.lock ./
COPY packages/core ./packages/core
COPY packages/api ./packages/api
COPY packages/sysadmin-api ./packages/sysadmin-api

# Install dependencies with cache mount
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --package swiss-ai-hub-sysadmin-api


# Runtime stage
FROM python:3.13-slim AS runtime

ARG VERSION

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PATH="/app/.venv/bin:$PATH" \
    AIHUB_VERSION=${VERSION}

ARG USERNAME=user
ARG USER_UID=1000
ARG USER_GID=$USER_UID

RUN groupadd --gid "$USER_GID" "$USERNAME" && \
    useradd --uid "$USER_UID" --gid "$USER_GID" -m -s /bin/bash "$USERNAME" && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy the venv and packages from the builder stage
COPY --from=builder --chown="$USERNAME:$USERNAME" /app /app

USER $USERNAME

EXPOSE 8000

WORKDIR /app

# Fully-qualified module target (not `app.main`) so there is no collision with
# packages/api's own app/main.py, which is also present in this image.
ENTRYPOINT ["gunicorn", "-w", "1", "-k", "uvicorn.workers.UvicornWorker", "--timeout=300", "-b", "0.0.0.0:8000", "--forwarded-allow-ips=*", "swiss_ai_hub.sysadmin_api.main:app"]
