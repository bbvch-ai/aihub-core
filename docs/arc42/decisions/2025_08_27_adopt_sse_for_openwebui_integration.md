# Adopt Server-Side Events (SSE) for Open-WebUI Integration

## Context

The Swiss AI Hub platform needed to provide better integration with Open-WebUI, a popular open-source web interface for
conversational AI. Previously, the integration relied on OpenAI-compatible endpoints that streamed simple text chunks,
which had significant limitations in communicating Swiss AI Hub's rich event system (ToolEvent, ThoughtEvent, etc.).

Open-WebUI has a robust internal event emission system that works naturally with streaming responses and Server-Side
Events. The existing OpenAI-compatible streaming approach could only communicate basic text content and didn't leverage
Swiss AI Hub's sophisticated event system or Open-WebUI's native streaming capabilities effectively.

The Swiss AI Hub already had a sophisticated event system built around NATS messaging, with rich event types
(ThoughtEvent, ChunkEvent, ToolEvent, HumanInTheLoopRequestEvent, etc.) that needed to be efficiently translated into
Open-WebUI's native data structures for optimal user experience.

## Decision Drivers

- **Rich Event Communication**: OpenAI-compatible endpoints only support text chunks, while Swiss AI Hub has rich events
  (tools, thoughts, retrieval) that needed native representation in Open-WebUI
- **Simplified Integration Architecture**: SSE provides a simpler unidirectional streaming model that naturally closes
  when conversations end, avoiding complex state management and event filtering required by WebSocket approaches
- **Better Event Translation**: Swiss AI Hub's event system needed to be cleanly translated into Open-WebUI's expected
  data structures without losing fidelity
- **Event Scope Binding**: SSE streams are naturally bound to specific user messages and auto-close when conversations
  end, providing clean event lifecycle management
- **HTTP-based Communication**: SSE uses standard HTTP, making it more compatible with proxies, load balancers, and
  existing web infrastructure
- **Event-Driven Architecture Alignment**: Both Swiss AI Hub and Open-WebUI are built around event-driven patterns, and
  SSE provides a natural bridge between them

## Decision

We will implement Server-Side Events (SSE) streaming endpoints alongside the existing WebSocket infrastructure to
provide native Open-WebUI integration.

### Decision 1: SSE Streaming Endpoints

Create dedicated SSE streaming endpoints in the Swiss AI Hub API:

1. **Agent Event Streaming**: Endpoint pattern `/api/v1/agents/{agent_class}/{agent_id}/{event_name}/stream`
2. **Native Swiss AI Hub Event Format**: Stream events in Swiss AI Hub's native event format rather than trying to adapt
   them to generic formats
3. **Query Parameter Support**: Use `thread_id` and `display_id` query parameters for context identification
4. **Standard HTTP POST**: Use POST requests with JSON payloads for event initiation

### Decision 2: Open-WebUI Pipeline Architecture

Implement a sophisticated Open-WebUI pipeline that:

1. **Event-Driven Processing**: Use Chain of Responsibility pattern for handling different Swiss AI Hub event types
2. **Streaming State Management**: Implement proper state management for content blocks (text, thinking, tool execution)
3. **Content Block Architecture**: Abstract content blocks with proper inheritance hierarchy (TextBlock, ThinkingBlock,
   ToolBlock)
4. **HTML Serialization**: Convert Swiss AI Hub events into Open-WebUI compatible HTML structures

### Decision 3: Event Translation Layer

Create a comprehensive event translation system:

1. **Event Handler Chain**: Specialized handlers for each Swiss AI Hub event type (ThoughtEventHandler,
   ChunkEventHandler, ToolEventHandler, etc.)
2. **Open-WebUI Event Emission**: Translate Swiss AI Hub events into Open-WebUI's expected event format
3. **Content Aggregation**: Properly aggregate streaming content and manage block completion states
4. **Human-in-the-Loop Support**: Full support for interactive events that require user input

### Decision 4: Maintain WebSocket Compatibility

Keep the existing WebSocket infrastructure:

1. **Parallel Implementation**: SSE endpoints complement rather than replace WebSocket functionality
2. **Frontend Compatibility**: Web frontend continues to use WebSocket for bidirectional communication
3. **Gradual Migration**: Allow gradual adoption of SSE where it provides benefits

## Consequences

### Positive

- **Simpler Open-WebUI Integration**: Pipeline implementation is more straightforward and aligns with Open-WebUI's
  streaming architecture
- **Better Performance**: SSE has lower overhead than WebSocket for unidirectional streaming use cases
- **Native Event Support**: Swiss AI Hub's rich event system (thoughts, tools, retrieval) translates cleanly to
  Open-WebUI's interface
- **HTTP Infrastructure Compatibility**: SSE works seamlessly with existing HTTP infrastructure (proxies, CDNs, load
  balancers)
- **Reduced Connection Management**: No need to manage connection lifecycle, authentication handshakes, or reconnection
  logic
- **Event Fidelity**: Native Swiss AI Hub event format preserves all event metadata and structure
- **Development Experience**: Easier to debug and test than WebSocket connections

### Negative

- **Dual Communication Channels**: Maintaining both SSE and WebSocket increases complexity in the API layer
- **Unidirectional Limitation**: SSE is unidirectional, requiring separate HTTP requests for client→server communication
- **Browser Support**: Slightly less universal browser support compared to WebSocket (though still excellent for modern
  browsers)
- **Event Ordering**: Potential complexity in ensuring proper event ordering in high-throughput scenarios

### Neutral

- **Protocol Specialization**: Different communication protocols optimized for different use cases (SSE for streaming,
  WebSocket for bidirectional)
- **Client Diversity**: Different clients can choose the most appropriate communication method
- **Infrastructure Requirements**: Both approaches require similar server-side infrastructure capabilities

## Implementation Notes

This decision enables:

- Native Open-WebUI pipeline: Complex event processing with proper content management
- Rich Swiss AI Hub event streaming: Full support for thoughts, tools, retrieval, and human-in-the-loop interactions
- Simplified integration: Single HTTP request initiates streaming conversation with agent
- Better observability: Standard HTTP request/response patterns with streaming bodies
