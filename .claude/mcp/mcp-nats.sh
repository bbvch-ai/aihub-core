#!/bin/bash
set -e
# NATS MCP — proper MCP server for NATS messaging system integration.
# Provides message viewing, subject inspection, JetStream stream management,
# and monitoring. NATS is the event-driven backbone for the Swiss AI Agent Protocol.
#
# Uses the certified mcp-nats server (sinadarbouy/mcp-nats) via Docker.
# Connection uses NATS_TOKEN from .env for authentication.
#
# Auth strategy: mcp-nats supports credentials, user/password, and anonymous modes.
# Our NATS uses token auth. We embed the token in the URL (nats://token@host:port)
# and use anonymous mode, so account_name="anonymous" in all tool calls.
#
# Workaround: The cnadb/mcp-nats Docker image bundles an ARM64 nats CLI binary
# even in the amd64 image (upstream packaging bug). We auto-download the correct
# nats CLI for the host architecture and mount it into the container.
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/../.."
if [[ -f .env ]]; then
  # shellcheck disable=SC1091
  source .env 2>/dev/null
fi

# .env.dev uses NATS_ENDPOINT for the connection URL and NATS_TOKEN for auth.
NATS_BASE="${NATS_ENDPOINT:-${NATS_URL:-nats://localhost:4222}}"

# Embed token in URL for auth (nats://token@host:port).
# The nats CLI authenticates via the URL's userinfo field.
if [[ -n "$NATS_TOKEN" ]]; then
  NATS_CONNECT="${NATS_BASE/nats:\/\//nats:\/\/${NATS_TOKEN}@}"
else
  NATS_CONNECT="$NATS_BASE"
fi

# --- nats CLI workaround ---
# Download correct nats CLI if not cached. Pinned version for reproducibility.
NATS_CLI_VERSION="0.3.1"
NATS_CLI_CACHE="$SCRIPT_DIR/bin"
NATS_CLI_BIN="$NATS_CLI_CACHE/nats"

if [[ ! -x "$NATS_CLI_BIN" ]]; then
  ARCH=$(uname -m)
  case "$ARCH" in
    x86_64)  NATS_ARCH="amd64" ;;
    aarch64) NATS_ARCH="arm64" ;;
    *)       echo "Unsupported architecture: $ARCH" >&2; exit 1 ;;
  esac
  mkdir -p "$NATS_CLI_CACHE"
  NATS_URL_DL="https://github.com/nats-io/natscli/releases/download/v${NATS_CLI_VERSION}/nats-${NATS_CLI_VERSION}-linux-${NATS_ARCH}.zip"
  echo "Downloading nats CLI v${NATS_CLI_VERSION} (${NATS_ARCH})..." >&2
  curl -sL "$NATS_URL_DL" -o "$NATS_CLI_CACHE/nats-cli.zip"
  unzip -oq "$NATS_CLI_CACHE/nats-cli.zip" -d "$NATS_CLI_CACHE/tmp"
  mv "$NATS_CLI_CACHE/tmp"/*/nats "$NATS_CLI_BIN"
  chmod +x "$NATS_CLI_BIN"
  rm -rf "$NATS_CLI_CACHE/tmp" "$NATS_CLI_CACHE/nats-cli.zip"
  echo "nats CLI cached at $NATS_CLI_BIN" >&2
fi

exec docker run -i --rm --init \
  --network=host \
  -v "$NATS_CLI_BIN:/usr/local/bin/nats:ro" \
  -e "NATS_URL=$NATS_CONNECT" \
  -e "NATS_NO_AUTHENTICATION=true" \
  cnadb/mcp-nats --transport stdio
