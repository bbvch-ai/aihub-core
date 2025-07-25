# syntax = docker/dockerfile:1.2

# Build stage
FROM python:3.11-slim AS builder

ARG PIPELINE=default_rag_pipeline


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
    curl -sSL https://install.python-poetry.org | python3 - --version ${POETRY_VERSION} && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY aihub_pipeline/app/${PIPELINE} ./aihub_pipeline/app/${PIPELINE}
COPY aihub_pipeline ./aihub_pipeline
COPY aihub_pipeline/Makefile ./aihub_pipeline/Makefile
COPY aihub_pipeline/poetry.lock ./aihub_pipeline/poetry.lock
COPY aihub_pipeline/pyproject.toml ./aihub_pipeline/pyproject.toml
COPY aihub_lib ./aihub_lib

COPY Makefile switch_dependencies.py pyproject.toml ./

RUN poetry install
RUN make use-local-core
RUN rm Makefile switch_dependencies.py pyproject.toml

# Set the working directory
WORKDIR /app/aihub_pipeline
RUN poetry install




# --- Runtime stage ---
FROM python:3.11-slim AS runtime

ARG PIPELINE=default_rag_pipeline
ENV PIPELINE_NAME=${PIPELINE}

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
    DAGSTER_HOME=/dagster_home

# Setup users
ARG USERNAME=user
ARG USER_UID=1000
ARG USER_GID=$USER_UID

# Create user group and user
RUN groupadd --gid "$USER_GID" "$USERNAME" && \
    useradd --uid "$USER_UID" --gid "$USER_GID" -m -s /bin/bash "$USERNAME"

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    sudo \
    tree \
    vim \
    iputils-ping \
    libasound2 \
    make \
    curl && \
    curl -sSL https://install.python-poetry.org | python3 - --version ${POETRY_VERSION} && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Give sudo access to the user
RUN echo "$USERNAME ALL=(root) NOPASSWD:ALL" > /etc/sudoers.d/"$USERNAME" && \
    chmod 0440 /etc/sudoers.d/"$USERNAME"

ENV DAGSTER_HOME=/dagster_home
RUN mkdir -p $DAGSTER_HOME

# Set the working directory
WORKDIR /app

# Copy application code and configuration files
COPY --from=builder /app /app

WORKDIR $DAGSTER_HOME

# Expose necessary port
EXPOSE 4000

# Start the application
ENTRYPOINT exec poetry run dagster api grpc -h 0.0.0.0 -p 4000 -m aihub_pipeline.app.${PIPELINE_NAME}
