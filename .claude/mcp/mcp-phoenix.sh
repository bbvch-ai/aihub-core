#!/bin/bash
set -e
cd "$(dirname "$0")/../.."
# Phoenix AI observability — query traces, view LLM call details, analyze agent performance
exec npx -y mcp-remote@latest http://localhost:6006/mcp
