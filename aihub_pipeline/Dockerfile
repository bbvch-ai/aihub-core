# syntax = docker/dockerfile:1.2

# Build stage
FROM python:3.13-slim AS builder

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

COPY Makefile switch_dependencies.py pyproject.toml ./
COPY aihub_pipeline ./aihub_pipeline
COPY aihub_lib ./aihub_lib
# TODO: remove once plugin separated!
COPY aihub_doc/mdformat-vuepress ./aihub_doc/mdformat-vuepress

RUN poetry install
RUN make use-local-core
RUN rm Makefile switch_dependencies.py pyproject.toml

# Set the working directory
WORKDIR /app/aihub_pipeline
RUN poetry install

RUN rm -rf ~/.cache/pypoetry ~/.cache/pip /tmp/poetry_cache


# --- Runtime stage ---
FROM python:3.13-slim AS runtime

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
EXPOSE 8000

# Start the application
ENTRYPOINT ["make", "dagster-webserver"]