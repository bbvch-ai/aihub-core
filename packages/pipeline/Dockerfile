# Build stage
FROM python:3.14-slim AS builder

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

# Copy workspace config + relevant packages
COPY pyproject.toml uv.lock ./
COPY packages/pipeline ./packages/pipeline
COPY packages/core ./packages/core

# Install dependencies with cache mount
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --package swiss-ai-hub-pipeline


# Runtime stage
FROM python:3.14-slim AS runtime

ARG VERSION

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PATH="/app/.venv/bin:$PATH" \
    AIHUB_VERSION=${VERSION}

# Setup users
ARG USERNAME=user
ARG USER_UID=1000
ARG USER_GID=$USER_UID

# Create user group and user
RUN groupadd --gid "$USER_GID" "$USERNAME" && \
    useradd --uid "$USER_UID" --gid "$USER_GID" -m -s /bin/bash "$USERNAME" && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    mkdir -p /dagster_home && \
    chown "$USERNAME:$USERNAME" /dagster_home

ENV DAGSTER_HOME=/dagster_home

WORKDIR /app

COPY --from=builder --chown="$USERNAME:$USERNAME" /app /app

USER $USERNAME

WORKDIR "$DAGSTER_HOME"

# Expose necessary port
EXPOSE 8000

# Entrypoint is defined in docker-compose for webserver and daemon
