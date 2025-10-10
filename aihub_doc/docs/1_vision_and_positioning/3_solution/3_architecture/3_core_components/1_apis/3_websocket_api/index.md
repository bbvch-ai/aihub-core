---
title: WebSocket API
index: 3
---

# WebSocket API

## Overview

The WebSocket API provides a bidirectional, real-time communication channel for applications requiring immediate
feedback and live updates during agent execution. Unlike traditional request-response HTTP patterns, the WebSocket API
maintains persistent connections that enable the platform to push events to clients as they occur, supporting
interactive user experiences and real-time monitoring applications.

## Design Rationale

### Real-Time User Experience Requirements

Modern AI applications demand responsive interfaces that provide immediate feedback during agent execution. Users expect
to see:

- Agent thinking and reasoning steps as they occur
- Progressive streaming of response content
- Real-time status updates (processing, waiting for input, completed)
- Immediate notification of errors or issues

The WebSocket API fulfills these requirements by pushing events from the platform to connected clients with minimal
latency, typically measured in milliseconds rather than the seconds required for HTTP polling.

### Event-Driven Architecture Integration

The platform's core is built on NATS JetStream, an event-driven messaging system. The WebSocket API acts as a bridge,
translating internal NATS events into WebSocket messages that clients can consume. This architecture ensures:

- **Consistency**: All platform components observe the same event stream
- **Scalability**: Multiple WebSocket connections can subscribe to the same underlying event stream
- **Reliability**: Events are persisted in JetStream, enabling replay and recovery
- **Decoupling**: WebSocket clients are isolated from internal implementation details

### Connection Management Strategy

WebSocket connections are stateful and long-lived, requiring careful management:

- **Authentication on Connect**: The first message must contain a valid bearer token
- **Automatic Disconnection**: Invalid authentication results in immediate connection termination
- **Graceful Degradation**: Connection failures trigger automatic reconnection in client implementations
- **Resource Limits**: Per-user connection limits prevent abuse

## Core Capabilities

### 1. Event Streaming

**Endpoint**: `GET /events/ws`

**Connection Flow**:

1. **Client Initiates WebSocket Connection**: Standard WebSocket handshake to `/events/ws`
2. **Authentication**: First message must be JSON: `{"token": "Bearer <access_token>"}`
3. **Token Validation**: Server validates token and extracts user identity
4. **Connection Accepted**: Server confirms authentication success
5. **Event Subscription**: Server begins streaming relevant events to the client
6. **Bidirectional Communication**: Client can send subscription updates; server pushes events

**Important Security Constraint**: The WebSocket connection is **read-only for clients**. Clients can receive events but
cannot publish events through the WebSocket. Event publishing must be done through the REST API endpoints, ensuring
proper authorization and validation.

### 2. Event Types and Structure

Events streamed through the WebSocket API are structured, typed messages that represent state changes and activities
within the platform:

**Agent Events**:

- `agent.started` - Agent execution initiated
- `agent.thinking` - Agent performing reasoning or retrieval
- `agent.tool_call` - Agent invoking a tool or function
- `agent.response_chunk` - Incremental response content (streaming)
- `agent.completed` - Agent execution finished
- `agent.error` - Agent encountered an error

**Thread Events**:

- `thread.created` - New conversation thread created
- `thread.updated` - Thread metadata changed
- `thread.message_added` - New message added to thread
- `thread.agent_added` - Agent joined the thread
- `thread.user_added` - User joined the thread

**Process Events**:

- `process.started` - Process execution initiated
- `process.step_completed` - Process step finished
- `process.waiting_for_input` - Process requires user input
- `process.completed` - Process execution finished
- `process.error` - Process encountered an error

**Event Structure**:

```json
{
  "event_type": "agent.response_chunk",
  "thread_id": "507f1f77bcf86cd799439011",
  "agent_class": "research_agent",
  "agent_id": "default",
  "timestamp": "2025-10-10T12:34:56.789Z",
  "payload": {
    "delta": "market analysis",
    "run_id": "507f191e810c19729de860ea"
  }
}
```

### 3. Filtering and Subscription Management

While the current implementation streams all events the user has access to, the architecture supports future
enhancements for fine-grained filtering:

**Potential Filtering Dimensions**:

- Thread-specific events (only events for threads the user is participating in)
- Agent-specific events (only events from specific agent classes or instances)
- Process-specific events (only events for processes the user owns or participates in)
- Event type filtering (only specific event types like completions or errors)

**Access Control**: The WebSocket manager filters events based on user permissions before streaming. Users only receive
events for resources they have permission to access:

- Events from threads they are members of or own
- Events from agents they have access to
- Events from processes they own or are participants in

## Authentication and Security

Bearer token authentication is required in the first message after connection establishment. Token validation uses the
same identity providers as REST endpoints. Hierarchical permission checks filter events before delivery, ensuring users
only receive events for resources they have access to (threads, agents, processes). Failed authentication results in
immediate connection termination with error code 4001.

**Security Constraint**: WebSocket connections are read-only for clients. Event publishing must occur through REST API
endpoints to ensure proper authorization and validation.

## Integration Patterns and Usage

The API supports three primary usage patterns:

**Real-Time User Interfaces**: Frontend applications establish persistent connections to receive live agent execution
updates, streaming responses, and status changes as they occur.

**Streaming Chat Completions**: Applications combine REST API requests to initiate agent actions with WebSocket
subscriptions to receive incremental response chunks for progressive display.

**Monitoring and Observability**: Administrative tools maintain connections for real-time platform monitoring, event
aggregation, and alert generation.

## Connection Management

Connections follow a standard lifecycle: client-initiated handshake, server-side authentication, active event streaming,
and eventual termination. Clients implement exponential backoff reconnection strategies with connection pooling at the
server side. The architecture scales horizontally across multiple API instances using sticky sessions and NATS-based
event broadcasting.

## Architecture Characteristics

The WebSocket API integrates directly with the platform's NATS JetStream event backbone, translating internal events to
client-consumable messages. Low-latency event delivery (10-50ms typical) supports real-time user experiences. The system
handles thousands of concurrent connections per instance with minimal resource overhead. Comprehensive instrumentation
captures connection metrics and authentication events through OpenTelemetry tracing.
