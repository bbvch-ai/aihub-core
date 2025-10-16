#!/bin/sh
set -euo pipefail

# Wait for Docker socket to be ready
for i in $(seq 1 30); do
  if docker -H unix:///var/run/docker.sock version >/dev/null 2>&1; then
    break
  fi
  echo "[health-events] waiting for dockerd..." >&2
  sleep 1
done

# Get hostname
HOST_NAME=$(docker info --format "{{.Name}}")

# Ensure log directory and file exist
mkdir -p /var/log/docker-health
touch /var/log/docker-health/events.ndjson

# Stream health events and add host.name field
docker -H unix:///var/run/docker.sock events \
  --since 15m \
  --filter event=health_status \
  --format "{{json .}}" \
  | sed "s/\"name\":\"\\([^\"]*\\)\"/\"name\":\"\\1\",\"host.name\":\"$HOST_NAME\"/" \
  | tee -a /var/log/docker-health/events.ndjson