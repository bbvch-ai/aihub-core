FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:0.10.4 /uv /uvx /bin/

ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY packages/backup/pyproject.toml ./packages/backup/pyproject.toml
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project --package swiss-ai-hub-backup

COPY packages/backup/swiss_ai_hub ./packages/backup/swiss_ai_hub

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --package swiss-ai-hub-backup

ENV DAGSTER_HOME=/dagster_home \
    PATH="/app/.venv/bin:$PATH"
RUN mkdir -p /dagster_home

COPY packages/backup/workspace.yaml /etc/dagster/workspace.yaml

EXPOSE 4266
