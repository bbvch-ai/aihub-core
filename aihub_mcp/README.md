# aihub_mcp

Full-featured MCP (Model Context Protocol) server for Swiss AI Hub, bridging the Swiss AI Agent Protocol with MCP.

## Features

- **Agents as MCP Tools**: Each registered agent is exposed as an MCP tool with dynamically generated schemas
- **Human-in-the-Loop via Elicitation**: HITL requests translate seamlessly to MCP elicitation
- **LLM Sampling**: Agents can request completions from the MCP client's LLM
- **Progress Streaming**: Real-time streaming of agent thoughts and output chunks
- **Dual Transport**: Streamable HTTP (recommended) and SSE for backward compatibility

## Quick Start

```bash
# Install dependencies
poetry install

# Run the MCP server (production)
MCP_API_KEY=your-secret-key make run-prod

# Or run the playground (no auth, for local testing)
make playground
```

## Configuration

Set environment variables or use `.env`:

```bash
# Server binding (default 127.0.0.1 for security; use 0.0.0.0 for network access)
MCP_HOST=127.0.0.1
MCP_PORT=8001

# Authentication (required when REQUIRE_AUTH=true)
MCP_API_KEY=your-api-key
MCP_REQUIRE_AUTH=true

# Infrastructure (uses shared lib settings - NATS_ENDPOINT, REDIS_URL)
```

## MCP Client Configuration

Add to your MCP client's configuration (e.g., Claude Code `.mcp.json`):

```json
{
  "mcpServers": {
    "aihub_agents": {
      "type": "http",
      "url": "http://localhost:8001/mcp"
    }
  }
}
```

## Development

```bash
# Format and lint
make pr-ready

# Run tests
make test

# Run with coverage
make test-cov
```

## Architecture

See [AGENTS.md](./AGENTS.md) for detailed architecture documentation.
