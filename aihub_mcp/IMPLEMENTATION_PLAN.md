# aihub_mcp Implementation Plan

## Overview

This plan outlines the implementation of a full-featured MCP (Model Context Protocol) server that bridges the Swiss AI Agent Protocol (SAAP) with MCP, enabling external clients (Claude Code, Cursor, VS Code extensions) to interact with AI Hub agents as first-class MCP tools.

## Architecture

### High-Level Design

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
| Agent needs LLM | `sampling/createMessage` | Server → Client |

## Package Structure

```
aihub_mcp/
├── aihub_mcp/
│   ├── __init__.py
│   ├── server/
│   │   ├── __init__.py
│   │   ├── MCPServer.py              # Main FastMCP server
│   │   ├── AgentToolRegistry.py      # Dynamic agent → MCP tool registration
│   │   └── ResourceRegistry.py       # Agent metadata resources
│   ├── translation/
│   │   ├── __init__.py
│   │   ├── EventTranslator.py        # SAAP ↔ MCP event translation
│   │   ├── ElicitationHandler.py     # HITL ↔ MCP elicitation
│   │   ├── SamplingBridge.py         # Agent LLM → Client LLM routing
│   │   └── ProgressStreamer.py       # Chunk/Thought → Progress notifications
│   ├── discovery/
│   │   ├── __init__.py
│   │   ├── AgentDiscoveryService.py  # Subscribe to agent discovery events
│   │   └── PromptRegistry.py         # Agent prompt templates
│   ├── auth/
│   │   ├── __init__.py
│   │   └── ApiKeyAuth.py             # API key authentication
│   ├── runners/
│   │   ├── __init__.py
│   │   └── MCPRunner.py              # Standalone MCP server runner
│   └── settings/
│       ├── __init__.py
│       └── MCPSettings.py            # Configuration via pydantic-settings
├── tests/
│   ├── __init__.py
│   ├── test_event_translation.py
│   ├── test_elicitation.py
│   ├── test_sampling.py
│   └── integration/
│       ├── test_claude_code.py
│       └── test_cursor.py
├── pyproject.toml
├── Makefile
├── README.md
└── AGENTS.md
```

## Implementation Steps

### Phase 1: Package Foundation

1. **Create package skeleton**
   - `pyproject.toml` with dependencies (fastmcp, aihub_lib, nats-py, etc.)
   - `Makefile` with standard targets (format, lint, test, pr-ready)
   - `AGENTS.md` scope documentation

2. **Implement MCPSettings**
   - Transport configuration (HTTP/SSE)
   - Authentication settings
   - NATS connection settings
   - Tracing configuration

### Phase 2: Core MCP Server

3. **Implement MCPServer (FastMCP)**
   - Initialize FastMCP with Streamable HTTP transport
   - Configure SSE transport for backward compatibility
   - Set up lifespan management
   - Mount at configurable path

4. **Implement AgentDiscoveryService**
   - Subscribe to `ClassDiscoveryRequestEvent/ResponseEvent` on NATS
   - Parse `AgentClassDiscoveryResponseEvent` schemas
   - Maintain registry of online agents

5. **Implement AgentToolRegistry**
   - Generate MCP tool schemas from `EventSpecs`
   - Register each agent as an MCP tool dynamically
   - Handle agent online/offline transitions

### Phase 3: Event Translation Layer

6. **Implement EventTranslator**
   - `UserMessageEvent` → Tool invocation handler
   - `StopEvent` → Tool success response
   - `ExceptionEvent` → Tool error response
   - Bidirectional serialization

7. **Implement ProgressStreamer**
   - Subscribe to DisplayEvents on NATS for active runs
   - Translate `ChunkEvent` → `ctx.report_progress()`
   - Translate `ThoughtEvent` → Progress with reasoning metadata

### Phase 4: Human-in-the-Loop via Elicitation

8. **Implement ElicitationHandler**
   - Detect `HumanInTheLoopRequestEvent` in SAAP stream
   - Translate to MCP elicitation request:
     - `hitl_type="input"` → `ctx.elicit(message, str)`
     - `hitl_type="confirmation"` → `ctx.elicit(message, bool)`
   - Receive elicitation response
   - Publish `HumanInTheLoopResponseEvent` to NATS

### Phase 5: LLM Sampling Support

9. **Implement SamplingBridge**
   - Create sampling capability in agents
   - When agent requests LLM completion:
     - Intercept sampling request event (new event type)
     - Call `ctx.sample()` to route to MCP client's LLM
     - Return completion to agent via NATS
   - Support tools in sampling (optional)

### Phase 6: Authentication & Security

10. **Implement ApiKeyAuth**
    - Extract API key from MCP request headers
    - Validate against configured keys
    - Map to user identity for SAAP events

### Phase 7: Observability

11. **Add OpenTelemetry instrumentation**
    - Trace MCP requests with span context
    - Link to SAAP event spans
    - Export to Phoenix

### Phase 8: Resources & Prompts

12. **Implement ResourceRegistry**
    - Expose agent metadata as MCP resources:
      - `agent://{agent_class}` → Agent schema
      - `agent://{agent_class}/{agent_id}` → Instance info
      - `agent://{agent_class}/{agent_id}/threads` → Thread list

13. **Implement PromptRegistry**
    - Surface agent-specific prompt templates
    - E.g., "Analyze Document", "Generate Report"

### Phase 9: Testing & Documentation

14. **Unit tests**
    - Event translation
    - Elicitation handling
    - Sampling bridge

15. **Integration tests**
    - Claude Code MCP client
    - Cursor MCP client
    - Manual testing scripts

16. **Documentation**
    - Architecture diagram in `aihub_doc/`
    - ADR for MCP bidirectional support
    - Usage examples in README

## Key Technical Decisions

### Transport Choice

**Primary: Streamable HTTP** (MCP spec 2025-03-26)
- Bi-directional communication
- Efficient chunked encoding
- Session management for stateful operations

**Secondary: SSE** (backward compatibility)
- For clients that don't support Streamable HTTP

### Integration Approach

**Standalone server** that can be:
1. Run independently (for dedicated MCP endpoint)
2. Mounted into `aihub_api` alongside existing MCP (for unified deployment)

### State Management

- Use existing `RunContext` and `ThreadContext` from SAAP
- MCP session → SAAP Thread mapping
- No additional state stores required

### Sampling Implementation

Two options (recommend Option A):

**Option A: New Sampling Event Type**
```python
class SamplingRequestEvent(ControlEvent):
    messages: list[dict]
    max_tokens: int | None

class SamplingResponseEvent(ControlEvent):
    content: str
    model: str
```

**Option B: Context-based sampling**
- Pass sampling capability via RunContext
- Agent calls `await run_context.sample(...)`

### Authentication

- API key authentication (header-based)
- Reuse existing OAuth2/OIDC for future enhancement

## Dependencies

```toml
[tool.poetry.dependencies]
python = ">=3.13, <3.14"
fastmcp = "^2.11.2"
aihub_lib = { git = "...", subdirectory = "aihub_lib" }
nats-py = "^2.9.0"
pydantic = "^2.10.3"
pydantic-settings = "^2.7.0"
opentelemetry-api = "^1.32.1"
opentelemetry-sdk = "^1.32.1"
```

## Success Criteria

From the Definition of Done:
- [ ] New `aihub_mcp` package created with proper Poetry configuration
- [ ] Streamable HTTP transport implemented per MCP spec 2025-03-26
- [ ] SSE transport implemented for backward compatibility
- [ ] Agents dynamically discovered and exposed as MCP tools
- [ ] `HumanInTheLoop.request/response` translated to/from MCP elicitation
- [ ] `sampling/createMessage` support with client LLM routing
- [ ] `ChunkEvent` and `ThoughtEvent` streamed as progress notifications
- [ ] `StopEvent` and `ExceptionEvent` properly terminate tool calls
- [ ] API key authentication
- [ ] Tracing instrumented for MCP requests
- [ ] Integration tests with Claude Code and Cursor as MCP clients
- [ ] Documentation in `aihub_doc/` with architecture diagrams

## Timeline Estimate

This is a significant implementation. The phases are ordered by dependency and can be executed incrementally.

## Open Questions

1. Should sampling support be opt-in per agent or global?
2. Do we need rate limiting on the MCP endpoint?
3. Should we support multiple concurrent HITL requests per session?
4. How should we handle agent discovery latency on MCP client connect?

---

**Ready for implementation approval.**
