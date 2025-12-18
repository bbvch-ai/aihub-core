# Build stage
FROM python:3.13-slim AS builder

ARG AGENT=expert_rag_agent
ARG VERSION

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    POETRY_VERSION=2.1.1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache \
    PATH="/opt/poetry/bin:$PATH"

# Install system dependencies and Poetry
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    make \
    openssh-client && \
    curl -sSL https://install.python-poetry.org | python3 - --version "${POETRY_VERSION}" && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

COPY aihub_agent/app/${AGENT} ./aihub_agent/app/${AGENT}
COPY aihub_agent/aihub_agent ./aihub_agent/aihub_agent
COPY aihub_agent/Makefile ./aihub_agent/Makefile
COPY aihub_agent/poetry.lock ./aihub_agent/poetry.lock
COPY aihub_agent/pyproject.toml ./aihub_agent/pyproject.toml
COPY aihub_lib ./aihub_lib

COPY Makefile switch_dependencies.py pyproject.toml ./

RUN poetry install --without dev && \
    make use-local-core && \
    rm Makefile switch_dependencies.py pyproject.toml

# Set the working directory
WORKDIR /app/aihub_agent

RUN poetry install && \
    rm -rf ~/.cache/pypoetry ~/.cache/pip /tmp/poetry_cache


# Runtime stage
FROM python:3.13-slim AS runtime

ARG AGENT=expert_rag_agent
ENV AGENT_NAME=${AGENT}
ARG VERSION


# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    POETRY_VERSION=2.1.1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache \
    PYTHONPATH=/app \
    PATH="/app/.venv/bin:/opt/poetry/bin:$PATH" \
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
    curl -sSL https://install.python-poetry.org | python3 - --version "${POETRY_VERSION}" && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy only the necessary code from the builder stage
COPY --from=builder --chown="$USERNAME:$USERNAME" /app /app

# Switch to non-root user
USER $USERNAME

# Set the working directory
WORKDIR /app/aihub_agent

# Start the server using Makefile
ENTRYPOINT ["sh", "-c", "exec poetry run python -m \"app.${AGENT_NAME}.main\""]
