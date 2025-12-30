# aihub_mcp - AI Agent Guide

## Overview

The `aihub_mcp` package implements a full-featured MCP (Model Context Protocol) server that bridges the Swiss AI Agent
Protocol (SAAP) with MCP, enabling external clients like Claude Code, Cursor, and VS Code extensions to interact with
AI Hub agents as first-class MCP tools.

## Architecture

### Core Components

```
aihub_mcp/
├── server/           # MCP server implementation
│   ├── MCPServer.py           # Main FastMCP server with transports
│   ├── AgentToolRegistry.py   # Dynamic agent → MCP tool registration
│   └── ResourceRegistry.py    # Agent metadata as MCP resources
├── translation/      # SAAP ↔ MCP event translation
│   ├── EventTranslator.py     # Core event translation logic
│   ├── ElicitationHandler.py  # HITL → MCP elicitation bridge
│   ├── SamplingBridge.py      # Agent LLM → Client LLM routing
│   └── ProgressStreamer.py    # Display events → Progress notifications
├── discovery/        # Agent discovery
│   ├── AgentDiscoveryService.py  # Subscribe to agent discovery
│   └── PromptRegistry.py      # Agent prompt templates
├── auth/             # Authentication
│   └── ApiKeyAuth.py          # API key authentication
├── runners/          # Server runners
│   └── MCPRunner.py           # Standalone server runner
└── settings/         # Configuration
    └── MCPSettings.py         # pydantic-settings configuration
```

### Event Translation Mapping

| SAAP Event | MCP Equivalent | Direction |
|------------|----------------|-----------|
| `UserMessageEvent` | Tool invocation request | Client → Server |
| `HumanInTheLoopRequestEvent` | `elicitation/request` | Server → Client |
| `HumanInTheLoopResponseEvent` | `elicitation/response` | Client → Server |
| `ChunkEvent` | Progress notification (partial) | Server → Client |
| `ThoughtEvent` | Progress notification (reasoning) | Server → Client |
| `StopEvent` | Tool execution complete | Server → Client |
| `ExceptionEvent` | Tool execution error | Server → Client |
| Sampling request | `sampling/createMessage` | Server → Client |

## Key Patterns

### Tool Registration from Agent Discovery

```python
# Agents are discovered via NATS and registered as MCP tools
async def register_agent_as_tool(agent_response: AgentClassDiscoveryResponseEvent):
    for start_event in agent_response.start_events:
        schema = start_event.event_schema

        @mcp.tool(name=f"{agent_response.agent_class}_{start_event.event_name}")
        async def agent_tool(**kwargs) -> str:
            # Translate to SAAP, publish, await response
            ...
```

### HITL → Elicitation Translation

```python
# When agent requests human input
if isinstance(event, HumanInTheLoopRequestEvent):
    if event.hitl_type == "input":
        result = await ctx.elicit(event.question, response_type=str)
    else:  # confirmation
        result = await ctx.elicit(event.question, response_type=bool)

    # Publish response back to SAAP
    response_event = HumanInTheLoopResponseEvent(
        response=result.data,
        request_event=event
    )
```

### Sampling Bridge

```python
# When agent needs LLM completion via client
sampling_response = await ctx.sample(
    messages=request.messages,
    max_tokens=request.max_tokens
)
# Route response back to agent via NATS
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MCP_HOST` | Server host (use `0.0.0.0` for network access) | `127.0.0.1` |
| `MCP_PORT` | Server port | `8001` |
| `MCP_PATH` | Endpoint path | `/mcp` |
| `MCP_TRANSPORT` | Transport type (`http`, `sse`) | `http` |
| `MCP_DEBUG` | Enable debug mode | `false` |
| `MCP_API_KEY` | API key for authentication | Required in production |
| `MCP_API_KEYS` | Additional API keys (comma-separated) | `[]` |
| `MCP_REQUIRE_AUTH` | Require authentication | `true` |
| `MCP_RATE_LIMIT_REQUESTS_PER_MINUTE` | Rate limit (0 to disable) | `60` |
| `MCP_MASK_SENSITIVE_DATA` | Mask sensitive data in logs | `true` |
| `MCP_AGENT_TIMEOUT_SECONDS` | Agent execution timeout | `300.0` |
| `MCP_NATS_URL` | NATS server URL | `nats://localhost:4222` |
| `MCP_TRACING_ENABLED` | Enable OpenTelemetry tracing | `true` |

### Security Notes

- **Production Mode**: When `MCP_DEBUG=false` (default), API keys are required unless `MCP_REQUIRE_AUTH=false`
- **Network Access**: Default host is `127.0.0.1` (localhost only). Set to `0.0.0.0` for external access, but ensure authentication is configured
- **Rate Limiting**: Enabled by default at 60 requests/minute per client
- **Data Masking**: Sensitive data (API keys, passwords, emails, etc.) is automatically masked in logs

## Running the Server

```bash
# Standalone
cd aihub_mcp
poetry install
make run

# Or directly
poetry run python -m aihub_mcp.main
```

## Integration with aihub_api

The MCP server can be mounted within `aihub_api` for unified deployment:

```python
from aihub_mcp import MCPRunner
from aihub_mcp.settings.MCPSettings import MCPSettings

runner = MCPRunner(MCPSettings())
mcp_app = runner.create_app()
# Mount alongside existing API
```

## Testing

```bash
# Unit tests
make test

# With coverage
make test-cov

# Integration tests (requires running services)
poetry run pytest -m integration
```

## Related Documentation

- [MCP Specification](https://spec.modelcontextprotocol.io/)
- [FastMCP Documentation](https://gofastmcp.com/)
- [Swiss AI Agent Protocol](../aihub_doc/docs/2_platform/2_architecture/3_swiss_ai_agent_protocol/)
- [Existing MCP ADR](../aihub_doc/arc42/decisions/2025_07_09_adopt_mcp_protocol.md)
