# Custom Postgres image: upstream pgvector + pg_repack server-side extension.
#
# pg_repack is required by the maintenance subsystem in packages/backup
# (postgres_repack handler) to physically reclaim disk pages from the dagster
# database after large DELETEs. The official pgvector image does not ship
# pg_repack; we extend it with the matching apt package and the extension
# files become available on the server filesystem.
#
# The CREATE EXTENSION statement that registers pg_repack inside the dagster
# database lives in the pg-init script, run on first container boot.
FROM pgvector/pgvector:pg17

RUN apt-get update && \
    apt-get install -y --no-install-recommends postgresql-17-repack && \
    rm -rf /var/lib/apt/lists/*
