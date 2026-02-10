# Build stage
FROM python:3.13-slim AS builder
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
    make && \
    curl -sSL https://install.python-poetry.org | python3 - --version "${POETRY_VERSION}" && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*


# Set the working directory
WORKDIR /app

# Copy only the dependency files first
COPY Makefile switch_dependencies.py pyproject.toml ./
COPY aihub_api ./aihub_api
COPY aihub_lib ./aihub_lib

RUN poetry install --without dev && \
    make use-local-core-without-install && \
    rm Makefile switch_dependencies.py pyproject.toml

# Set the working directory
WORKDIR /app/aihub_api

RUN poetry lock && \
    poetry install && \
    rm -rf ~/.cache/pypoetry ~/.cache/pip /tmp/poetry_cache


# Runtime stage
FROM python:3.13-slim AS runtime

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
    AIHUB_API_VERSION=${VERSION}

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
    ffmpeg \
    make && \
    curl -sSL https://install.python-poetry.org | python3 - --version "${POETRY_VERSION}" && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy only the necessary code from the builder stage
COPY --from=builder --chown="$USERNAME:$USERNAME" /app /app

# Switch to non-root user
USER $USERNAME

# Expose port 8000
EXPOSE 8000

WORKDIR /app/aihub_api

# Start the server using Makefile
ENTRYPOINT ["make", "run-prod"]