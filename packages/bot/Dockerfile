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

# Copy workspace config + relevant packages
COPY pyproject.toml uv.lock ./
COPY packages/bot ./packages/bot
COPY packages/core ./packages/core

# Install dependencies with cache mount
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --package swiss-ai-hub-bot


# Runtime stage
FROM python:3.13-slim AS runtime

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
    curl \
    ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy only the necessary code from the builder stage
COPY --from=builder --chown="$USERNAME:$USERNAME" /app /app

# Switch to non-root user
USER $USERNAME

# Expose port 8001 (bot runs on 8001)
EXPOSE 8001

WORKDIR /app/packages/bot

ENTRYPOINT ["gunicorn", "-w", "1", "-k", "uvicorn.workers.UvicornWorker", "--timeout=300", "-b", "0.0.0.0:8001", "--forwarded-allow-ips=*", "app.main:app"]
