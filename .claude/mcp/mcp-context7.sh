#!/bin/bash
set -e
# Context7 — provides up-to-date, version-specific library documentation.
# Eliminates hallucinated APIs by injecting current docs for LlamaIndex, FastAPI,
# Pydantic, Dagster, PrimeVue, Nuxt, MongoEngine, NATS, and other project dependencies.
#
# Tools: resolve-library-id, query-docs
# No API key required for basic use. For higher rate limits, get a free key at
# https://context7.com/dashboard and set CONTEXT7_API_KEY in .env
cd "$(dirname "$0")/../.."
if [[ -f .env ]]; then
  # shellcheck disable=SC1091
  source .env 2>/dev/null
fi

args=()
if [[ -n "$CONTEXT7_API_KEY" ]]; then
  args+=(--api-key "$CONTEXT7_API_KEY")
fi

exec npx -y @upstash/context7-mcp "${args[@]}"
