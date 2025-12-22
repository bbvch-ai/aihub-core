---
title: Bidirectional MCP Server
---

# Bidirectional MCP Server (aihub_mcp)

The `aihub_mcp` module provides a full-featured MCP (Model Context Protocol) server that bridges the Swiss AI Agent
Protocol with MCP, enabling external clients like Claude Code, Cursor, and VS Code extensions to interact with AI Hub
agents as first-class MCP tools.

## Overview

Unlike the simple API wrapper MCP endpoint in `aihub_api`, this module implements bidirectional communication:

- **Human-in-the-Loop**: Agents can request user input via MCP elicitation
- **LLM Sampling**: Agents can use the MCP client's LLM for completions
- **Progress Streaming**: Real-time streaming of agent thoughts and output chunks
- **Dynamic Discovery**: Agents are automatically discovered and exposed as MCP tools

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      MCP Clients                                │
│              (Claude Code, Cursor, VS Code)                     │
└──────────────────────────┬──────────────────────────────────────┘
                           │ MCP Protocol (Streamable HTTP/SSE)
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                     aihub_mcp Server                            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────┐  │
│  │   MCPServer     │  │ EventTranslator │  │ SamplingBridge │  │
│  │   (FastMCP)     │  │  (SAAP ↔ MCP)   │  │ (LLM routing)  │  │
│  └─────────────────┘  └─────────────────┘  └────────────────┘  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────┐  │
│  │ AgentDiscovery  │  │ ElicitHandler   │  │ ProgressStream │  │
│  │ (Dynamic tools) │  │ (HITL ↔ Elicit) │  │ (Chunk/Thought)│  │
│  └─────────────────┘  └─────────────────┘  └────────────────┘  │
└──────────────────────────┬──────────────────────────────────────┘
                           │ NATS Pub/Sub (Swiss AI Agent Protocol)
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                      AI Hub Agents                              │
│              (RAGAgent, ChatAgent, etc.)                        │
└─────────────────────────────────────────────────────────────────┘
```

## Event Translation

The server translates between Swiss AI Agent Protocol events and MCP protocol:

| SAAP Event                    | MCP Equivalent           | Direction       |
| ----------------------------- | ------------------------ | --------------- |
| `UserMessageEvent`            | Tool invocation request  | Client → Server |
| `HumanInTheLoopRequestEvent`  | Elicitation request      | Server → Client |
| `HumanInTheLoopResponseEvent` | Elicitation response     | Client → Server |
| `ChunkEvent`                  | Progress notification    | Server → Client |
| `ThoughtEvent`                | Progress notification    | Server → Client |
| `StopEvent`                   | Tool execution complete  | Server → Client |
| `ExceptionEvent`              | Tool execution error     | Server → Client |
| Agent LLM request             | `sampling/createMessage` | Server → Client |

## Configuration

Set environment variables or create a `.env` file:

```bash
# Server
MCP_HOST=0.0.0.0
MCP_PORT=8001
MCP_PATH=/mcp
MCP_TRANSPORT=http  # or 'sse' for backward compatibility

# Authentication
MCP_API_KEY=your-secret-key

# NATS
NATS_URL=nats://localhost:4222

# Observability
MCP_TRACING_ENABLED=true
MCP_DEBUG=false
```

## Running the Server

### Standalone

```bash
cd aihub_mcp
poetry install
poetry run python -m aihub_mcp
```

### With Docker

```bash
docker run -p 8001:8001 aihub_mcp
```

## Client Configuration

### Claude Code

Add to `.mcp.json`:

```json
{
  "mcpServers": {
    "aihub_agents": {
      "type": "http",
      "url": "http://localhost:8001/mcp",
      "headers": {
        "X-API-Key": "your-api-key"
      }
    }
  }
}
```

### Cursor

Configure in Cursor settings → MCP Servers:

- URL: `http://localhost:8001/mcp`
- Type: HTTP
- API Key: Your configured key

## Features

### Dynamic Agent Discovery

Agents are automatically discovered via NATS and exposed as MCP tools. Each agent's start events become tools with
dynamically generated schemas.

```python
# Example: RAGAgent becomes an MCP tool
# Tool name: rag_agent_user_message
# Description: Chat with the RAGAgent...
```

### Human-in-the-Loop via Elicitation

When an agent workflow needs human input, the request is translated to MCP elicitation:

```python
# Agent code
return HumanInTheLoop.input.invoke("What document should I analyze?")

# MCP client sees elicitation request
# User provides input
# Response flows back to agent
```

### LLM Sampling

Agents can request completions from the MCP client's LLM:

```python
# Agent requests sampling
result = await ctx.sample("Summarize this document...")

# MCP client's LLM provides completion
# Result returned to agent
```

### Progress Streaming

`ChunkEvent` and `ThoughtEvent` stream as progress notifications:

```python
# Agent emits chunks
yield ChunkEvent(content="Processing...")

# MCP client sees real-time progress
```

## Security

### API Key Authentication

API keys are validated from request headers:

- `X-API-Key` header
- `Authorization: Bearer <token>` header

### Best Practices

1. Use strong, unique API keys per client
2. Enable HTTPS in production
3. Configure proper CORS origins
4. Monitor with tracing enabled

## Observability

OpenTelemetry instrumentation provides:

- Span traces for tool invocations
- Elicitation request/response traces
- Sampling request traces
- Progress event traces

View traces in Arize Phoenix (http://localhost:6006) when `MCP_TRACING_ENABLED=true`.

## Related

- [MCP Protocol Overview](../index.en.md)
- [Swiss AI Agent Protocol](../../2_architecture/3_swiss_ai_agent_protocol/index.en.md)
- [ADR: MCP Bidirectional Agent Interaction](../../../arc42/decisions/2025_12_22_mcp_bidirectional_agent_interaction.md)
