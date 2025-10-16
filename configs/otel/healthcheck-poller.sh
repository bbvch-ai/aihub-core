#!/bin/sh
set -e

# Install dependencies
apk add --no-cache wget curl jq docker-cli

# Get hostname
HOST_NAME=$(docker info --format '{{.Name}}')

# Download grpc_health_probe
GRPC_PROBE_URL="https://github.com/grpc-ecosystem/grpc-health-probe/releases/download/v0.4.24/grpc_health_probe-linux-amd64"
wget -qO /usr/local/bin/grpc_health_probe "$GRPC_PROBE_URL"
chmod +x /usr/local/bin/grpc_health_probe

# Function to log health event
log_health_event() {
  local name="$1"
  local status="$2"
  local from="$3"
  local ts=$(date +%s)
  local tsn=$(date +%s%N)

  echo "{\"Type\":\"container\",\"Action\":\"health_status: $status\",\"Actor\":{\"Attributes\":{\"name\":\"$name\",\"host.name\":\"$HOST_NAME\"}},\"id\":\"$name\",\"from\":\"$from\",\"time\":$ts,\"timeNano\":$tsn}" >> /var/log/docker-health/events.ndjson
}

# Function to check HTTP endpoint
check_http_endpoint() {
  local endpoint="$1"
  local name=$(echo "$endpoint" | cut -d: -f1)
  local url="http://$endpoint"

  if wget -q --spider "$url" 2>/dev/null; then
    log_health_event "$name" "healthy" "$url"
  else
    log_health_event "$name" "unhealthy" "$url"
  fi
}

# Function to check gRPC endpoint
check_grpc_endpoint() {
  local endpoint="$1"
  local name=$(echo "$endpoint" | cut -d: -f1)

  if /usr/local/bin/grpc_health_probe -addr="$endpoint" 2>/dev/null; then
    log_health_event "$name" "healthy" "grpc://$endpoint"
  else
    log_health_event "$name" "unhealthy" "grpc://$endpoint"
  fi
}

# Main polling loop
while true; do
  # Check HTTP endpoints
  echo "$ENDPOINTS" | while IFS= read -r endpoint; do
    [ -z "$endpoint" ] && continue
    check_http_endpoint "$endpoint"
  done

  # Check gRPC endpoints
  echo "$GRPC_ENDPOINTS" | while IFS= read -r endpoint; do
    [ -z "$endpoint" ] && continue
    check_grpc_endpoint "$endpoint"
  done

  sleep 60
done