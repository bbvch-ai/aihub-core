FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:0.10.4 /uv /uvx /bin/

ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# PostgreSQL 17 client tools (pg_dumpall, pg_dump, pg_restore, psql) from PGDG repo
# curl for healthcheck, gzip for pg_dumpall compression, unzip for nats CLI
RUN apt-get update && \
    apt-get install -y --no-install-recommends wget gnupg && \
    . /etc/os-release && \
    echo "deb http://apt.postgresql.org/pub/repos/apt ${VERSION_CODENAME}-pgdg main" \
        > /etc/apt/sources.list.d/pgdg.list && \
    wget -qO - https://www.postgresql.org/media/keys/ACCC4CF8.asc \
        | gpg --dearmor -o /etc/apt/trusted.gpg.d/pgdg.gpg && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        postgresql-client-17 \
        gzip \
        curl \
        unzip && \
    apt-get purge -y --auto-remove gnupg && \
    rm -rf /var/lib/apt/lists/*

# milvus-backup tool (official Zilliz backup/restore for Milvus)
ARG MILVUS_BACKUP_VERSION=0.5.11
ARG TARGETARCH
RUN ARCH=$([ "$TARGETARCH" = "arm64" ] && echo "arm64" || echo "x86_64") && \
    wget -q "https://github.com/zilliztech/milvus-backup/releases/download/v${MILVUS_BACKUP_VERSION}/milvus-backup_${MILVUS_BACKUP_VERSION}_Linux_${ARCH}.tar.gz" -O /tmp/milvus-backup.tar.gz && \
    tar -xzf /tmp/milvus-backup.tar.gz -C /usr/local/bin/ milvus-backup && \
    chmod +x /usr/local/bin/milvus-backup && \
    rm /tmp/milvus-backup.tar.gz

# nats CLI (official backup/restore tool for NATS JetStream streams)
ARG NATS_CLI_VERSION=0.3.1
RUN ARCH=$([ "$TARGETARCH" = "arm64" ] && echo "arm64" || echo "amd64") && \
    wget -q "https://github.com/nats-io/natscli/releases/download/v${NATS_CLI_VERSION}/nats-${NATS_CLI_VERSION}-linux-${ARCH}.zip" -O /tmp/nats-cli.zip && \
    unzip -j /tmp/nats-cli.zip "nats-${NATS_CLI_VERSION}-linux-${ARCH}/nats" -d /usr/local/bin/ && \
    chmod +x /usr/local/bin/nats && \
    rm -rf /tmp/nats-cli.zip

WORKDIR /app

# Install Python dependencies (lockfile from workspace root)
COPY pyproject.toml uv.lock ./
COPY aihub_backup/pyproject.toml ./aihub_backup/pyproject.toml
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --package aihub-backup

# Copy application code
COPY aihub_backup/aihub_backup ./aihub_backup/aihub_backup
COPY aihub_backup/milvus-backup.yaml /etc/backup/milvus-backup.yaml

# Dagster workspace and entrypoint
ENV DAGSTER_HOME=/dagster_home \
    PATH="/app/.venv/bin:$PATH"
RUN mkdir -p /dagster_home
# Store workspace.yaml outside DAGSTER_HOME so it survives volume mounts
COPY aihub_backup/workspace.yaml /etc/dagster/workspace.yaml
COPY aihub_backup/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

EXPOSE 3000

# NOTE: This container runs as root because it needs access to the Docker
# socket (/var/run/docker.sock) for container lifecycle management (stop,
# start, exec, cp). The host socket GID varies across systems, making a
# fixed non-root user unreliable. For production hardening, consider using
# a docker-socket-proxy (e.g. tecnativa/docker-socket-proxy) to limit the
# API surface exposed to this container.

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:3000/server_info || exit 1

ENTRYPOINT ["/app/entrypoint.sh"]
