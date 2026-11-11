# Build stage
FROM python:3.13-slim AS builder

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

# Third-party dependencies first: this layer is identical for every agent and only rebuilds when the lockfile
# or a package manifest changes, so the agent images share it through the build cache.
COPY pyproject.toml uv.lock ./
COPY packages/core/pyproject.toml packages/core/README.md packages/core/LICENSE ./packages/core/
COPY packages/agent/pyproject.toml packages/agent/README.md packages/agent/LICENSE ./packages/agent/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-workspace --package swiss-ai-hub-agent

COPY packages/core ./packages/core
COPY packages/agent/swiss_ai_hub ./packages/agent/swiss_ai_hub

# Declared after the shared layers: build args take part in the cache key of every later RUN.
ARG AGENT=knowledge_extraction_agent
COPY packages/agent/app/${AGENT} ./packages/agent/app/${AGENT}

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --package swiss-ai-hub-agent


# Runtime stage
FROM python:3.13-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PATH="/app/.venv/bin:$PATH"

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

ARG AGENT=knowledge_extraction_agent
ARG VERSION
ENV AGENT_NAME=${AGENT} \
    AIHUB_VERSION=${VERSION}

WORKDIR /app

# Copy only the necessary code from the builder stage
COPY --from=builder --chown="$USERNAME:$USERNAME" /app /app

# Switch to non-root user
USER $USERNAME

WORKDIR /app/packages/agent

ENTRYPOINT ["sh", "-c", "exec python -m \"app.${AGENT_NAME}.main\""]
