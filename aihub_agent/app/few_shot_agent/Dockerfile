# Build stage
FROM python:3.13-slim AS builder

ARG AGENT=few_shot_agent
ARG VERSION

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

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
COPY aihub_agent/app/${AGENT} ./aihub_agent/app/${AGENT}
COPY aihub_agent/aihub_agent ./aihub_agent/aihub_agent
COPY aihub_agent/pyproject.toml ./aihub_agent/pyproject.toml
COPY aihub_lib ./aihub_lib

# Install dependencies with cache mount
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --package aihub-agent


# Runtime stage
FROM python:3.13-slim AS runtime

ARG AGENT=few_shot_agent
ENV AGENT_NAME=${AGENT}
ARG VERSION

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PATH="/app/.venv/bin:$PATH" \
    AIHUB_AGENT_VERSION=${VERSION}

# Setup users
ARG USERNAME=user
ARG USER_UID=1000
ARG USER_GID=$USER_UID

# Create user group and user
RUN groupadd --gid "$USER_GID" "$USERNAME" && \
    useradd --uid "$USER_UID" --gid "$USER_GID" -m -s /bin/bash "$USERNAME" && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    ca-certificates \
    curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy only the necessary code from the builder stage
COPY --from=builder --chown="$USERNAME:$USERNAME" /app /app

# Switch to non-root user
USER $USERNAME

WORKDIR /app/aihub_agent

ENTRYPOINT ["sh", "-c", "exec python -m \"app.${AGENT_NAME}.main\""]
