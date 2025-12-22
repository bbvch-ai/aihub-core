# ADR: Full-Featured MCP Server for Bidirectional Agent Interaction

**Date:** 2025-12-22

**Status:** Accepted

## Context

The Swiss AI Hub currently exposes agents via an MCP endpoint in `aihub_api`, but this implementation functions as a
simple API wrapper. It doesn't support the bidirectional, interactive capabilities that make MCP powerful for agentic
workflows. External MCP clients (Claude Code, Cursor, VS Code extensions) connecting to our agents cannot:

1. Receive structured **human-in-the-loop requests** when agents need user input or approval
2. Provide **LLM sampling** to agents that need to leverage the client's model for completions
3. Handle **elicitation** for structured data collection during tool execution
4. Stream granular **progress updates** as agents execute multi-step workflows

This limits the value of our MCP endpoint to simple request-response patterns, missing the rich interactivity that the
MCP specification enables.

## Decision Drivers

1. **Interactivity**: Enable bidirectional communication between MCP clients and agents
2. **HITL Support**: Translate Swiss AI Agent Protocol HITL events to MCP elicitation
3. **Client LLM Access**: Allow agents to request completions from the MCP client's LLM
4. **Progress Visibility**: Stream agent thoughts and output chunks to clients
5. **Standard Compliance**: Follow MCP spec 2025-03-26 for Streamable HTTP transport
6. **Separation of Concerns**: Create a dedicated module rather than extending aihub_api

## Decision

Create a new `aihub_mcp` package that implements a full-featured MCP server bridging the Swiss AI Agent Protocol (SAAP)
with the Model Context Protocol (MCP).

### Architecture

```
MCP Clients (Claude Code, Cursor, VS Code)
              │
              ▼ MCP Protocol (Streamable HTTP/SSE)
┌─────────────────────────────────────────────┐
│            aihub_mcp Server                 │
│  ┌─────────────┐    ┌───────────────────┐  │
│  │  MCPServer  │    │  EventTranslator  │  │
│  │  (FastMCP)  │    │  (SAAP ↔ MCP)     │  │
│  └─────────────┘    └───────────────────┘  │
│  ┌─────────────┐    ┌───────────────────┐  │
│  │ Discovery   │    │  Elicitation +    │  │
│  │ Service     │    │  Sampling Bridge  │  │
│  └─────────────┘    └───────────────────┘  │
└─────────────────────────────────────────────┘
              │
              ▼ NATS Pub/Sub (Swiss AI Agent Protocol)
        AI Hub Agents (RAGAgent, ChatAgent, etc.)
```

### Event Translation

| SAAP Event                     | MCP Equivalent           | Direction        |
| ------------------------------ | ------------------------ | ---------------- |
| `UserMessageEvent`             | Tool invocation          | Client → Server  |
| `HumanInTheLoopRequestEvent`   | Elicitation request      | Server → Client  |
| `HumanInTheLoopResponseEvent`  | Elicitation response     | Client → Server  |
| `ChunkEvent`                   | Progress notification    | Server → Client  |
| `ThoughtEvent`                 | Progress notification    | Server → Client  |
| `StopEvent`                    | Tool completion          | Server → Client  |
| `ExceptionEvent`               | Tool error               | Server → Client  |
| Agent sampling request         | `sampling/createMessage` | Server → Client  |

### Key Components

1. **MCPServer**: FastMCP-based server with Streamable HTTP and SSE transports
2. **AgentDiscoveryService**: Subscribes to NATS discovery events, registers agents as MCP tools
3. **EventTranslator**: Bidirectional translation between SAAP events and MCP protocol
4. **ElicitationHandler**: Translates HITL requests to MCP elicitation
5. **SamplingBridge**: Routes agent LLM requests to MCP client's model
6. **ProgressStreamer**: Streams ChunkEvent/ThoughtEvent as progress notifications

### Technology Choices

- **FastMCP v2.11.2**: Already used in aihub_api, provides full MCP spec support
- **NATS**: Existing messaging backbone for Swiss AI Agent Protocol
- **Streamable HTTP**: Primary transport per MCP spec 2025-03-26
- **SSE**: Backward compatibility for older clients

## Consequences

### Positive

- Full MCP spec compliance with bidirectional capabilities
- Seamless HITL integration via elicitation
- Clients can provide LLM completions to agents (cost/privacy benefits)
- Real-time progress streaming for better UX
- Clean separation from existing aihub_api
- Agents become first-class citizens in MCP ecosystem

### Negative

- Additional service to deploy and maintain
- Complexity of event translation between two protocols
- Potential latency from NATS round-trips

### Neutral

- Requires clients to support elicitation and sampling (optional MCP features)
- May need additional documentation for MCP client configuration

## Alternatives Considered

### 1. Extend Existing MCP in aihub_api

**Rejected**: The existing implementation is tightly coupled to FastAPI route mapping. Adding bidirectional features
would complicate the clean API abstraction. A dedicated module provides better separation of concerns.

### 2. Implement Custom Protocol

**Rejected**: MCP is becoming a standard for AI tool integration. Using a custom protocol would limit interoperability
with existing tools and require custom client development.

### 3. Use WebSocket Instead of MCP

**Rejected**: MCP provides structured semantics for AI interactions (tools, resources, prompts, elicitation, sampling)
that would need to be reinvented with raw WebSocket.

## Related Decisions

- [2025_07_09_adopt_mcp_protocol.md](./2025_07_09_adopt_mcp_protocol.md) - Initial MCP adoption
- Swiss AI Agent Protocol documentation - Core event-driven architecture

## References

- [MCP Specification 2025-03-26](https://spec.modelcontextprotocol.io/)
- [FastMCP Documentation](https://gofastmcp.com/)
- Swiss AI Agent Protocol: `aihub_doc/docs/2_platform/2_architecture/3_swiss_ai_agent_protocol/`
