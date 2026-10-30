---
title: Dynamic Agent and Process Endpoints
---

# Dynamic Agent and Process Endpoints :rocket: :100:

::: info **TL;DR - What are Dynamic Endpoints?**
The Swiss AI Hub automatically creates REST API endpoints on-the-fly based on the agents and processes available in your
system. When a new agent or process comes online, the API gateway instantly generates custom endpoints tailored to that
specific component's capabilities, eliminating the need for manual API development and ensuring your system stays
perfectly synchronized.
:::

## What are Dynamic Endpoints and How Do They Work? :brain:

Dynamic Agent and Process Endpoints represent a revolutionary approach to API generation in distributed AI systems.
Instead of pre-defining static API routes, the Swiss AI Hub employs **intelligent endpoint discovery services** that:

- **Continuously scan** the NATS message bus for available agents and processes
- **Automatically generate** REST endpoints based on each component's event specifications
- **Dynamically register** these endpoints with the FastAPI application at runtime
- **Maintain synchronization** between your running services and available API endpoints

This system leverages two core discovery services:

- **`AgentEndpointsDiscoveryService`**: Creates endpoints like
  `/agents/classes/{AgentClass}/instances/{agent_id}/{EventName}` for sending events to specific agents
- **`ProcessEndpointsDiscoveryService`**: Generates endpoints like `/processes/{process_class}/{process_id}/{route}` for
  human and program interaction with processes

The discovery process uses **NATS-based service discovery** to query running components about their capabilities. Each
agent announces, for every event it accepts, the schema of what an API caller sends: the event without the fields the
server fills in (the caller, the locale, ids and timestamps), and with the inputs the event converts itself, such as
files sent inline. The **Jambo SchemaConverter** turns that schema into the Pydantic model that powers the fully-typed,
documented endpoint.

## Why This is a Game-Changer for Your AI Strategy :trophy:

This feature eliminates one of the biggest barriers to scaling AI systems - **API development bottlenecks**:

**🔗 Zero-Configuration API Generation**: New agents and processes automatically expose their capabilities through REST
APIs without any manual development. Deploy a new agent, and its endpoints appear instantly in your API documentation.

**🧠 Type-Safe Dynamic Integration**: Every dynamic endpoint is fully typed using Pydantic models generated from event
schemas, providing automatic validation, serialization, and comprehensive OpenAPI documentation.

**🛡️ Enterprise-Grade Security**: Dynamic endpoints inherit all security features including role-based access control,
authentication, and fine-grained permissions, ensuring new capabilities are secure by default.

**⚡ Real-Time System Adaptation**: Your API automatically adapts to system changes - when agents scale up or down, their
endpoints appear or disappear accordingly, keeping your integration layer perfectly synchronized.

**🌐 Seamless External Integration**: External systems and webhooks can interact with any agent or process through
predictable REST endpoints, enabling powerful integrations with third-party services and business systems.

::: details **Setting Up and Using Dynamic Endpoints**
## Configuration Requirements

Dynamic endpoints are enabled automatically when you start the Swiss AI Hub with the full infrastructure stack:

1. **NATS Message Bus**: Required for service discovery communication
2. **API Gateway**: The `aihub_api` service with `lifetime_manager` enabled
3. **Discovery Services**: Automatically started by the lifetime manager

## Agent Endpoint Generation

For each discovered agent, the system creates endpoints following this pattern:

```
POST /api/v1/{tenant_id}/agents/classes/{AgentClass}/instances/{agent_id}/{EventName}
POST /api/v1/{tenant_id}/agents/classes/{AgentClass}/instances/{agent_id}/{EventName}/stream
```

The first waits for the run to finish and returns its stop event; the second streams every event of the run as
server-sent events.

**Example**: An instance `customer-support` of the `RAGAgent` class, which accepts `UserMessageEvent`, gets:

```
POST /api/v1/{tenant_id}/agents/classes/RAGAgent/instances/customer-support/UserMessageEvent
```

## Process Endpoint Generation

For each discovered process, the system creates endpoints based on the process definition:

```
GET  /api/v1/{tenant_id}/processes/{process_class}/{process_id}/{route}         # Get form
POST /api/v1/{tenant_id}/processes/{process_class}/{process_id}/{route}         # Submit form
GET  /api/v1/{tenant_id}/processes/{process_class}/{process_id}/{walkthrough_id}/{route}  # Continue process
POST /api/v1/{tenant_id}/processes/{process_class}/{process_id}/{walkthrough_id}/{route}  # Submit continuation
```

## Available Capabilities

Dynamic endpoints provide:

- **Full OpenAPI Documentation**: Every endpoint appears in `/docs` with complete request/response schemas
- **Type Validation**: The whole request is validated before anything happens with it. Only then does the event convert
  what it accepts in another shape, such as storing files sent inline
- **Authentication**: Inherited from the base controller security model
- **Error Handling**: Standardized error responses and HTTP status codes
- **Caching**: Built-in response caching for discovery-related operations

## Security and Best Practices

**Access Control**:

- Agent endpoints require `aihub.user.agent.{agent_class}.{agent_id}` permission
- Process endpoints require `aihub.user.process.{process_class}.{process_id}` permission

**Rate Limiting**: Discovery services run on configurable intervals (default: 60 seconds) to balance responsiveness with
system load

**Monitoring**: All dynamic endpoint usage is logged and traced through standard Swiss AI Hub observability tools

**Performance**: Dynamic endpoints are cached and only regenerated when the system topology changes
:::

## Getting Started

To begin using dynamic endpoints in your Swiss AI Hub:

1. **Start the Infrastructure**: Ensure NATS and the API gateway are running with the standard Docker Compose setup
2. **Deploy Agents/Processes**: Any agent or process that connects to NATS will automatically get endpoints
3. **Discover Endpoints**: Check `/api/v1/active/docs` to see all dynamically generated endpoints
4. **Integrate**: Use the standard REST endpoints to integrate with external systems or build custom frontends

The dynamic endpoint system transforms the Swiss AI Hub from a static API into a living, adaptive integration layer that
grows with your AI capabilities.

## Sending Files to an Agent

Events that carry files, such as `UserMessageEvent`, accept each entry of `files` in one of two forms, and both can be
mixed in one request:

- **Inline**: `filename`, `file_type` (the MIME type) and `content`, the file encoded as base64. The API stores the file
  in the agent's file bucket before the agent is called, and the agent receives its reference like any uploaded file.
- **Uploaded beforehand**: `filename`, `file_type` and the `file_id` returned by the agent's file upload endpoints.

```bash
curl -X POST "https://<host>/api/v1/active/agents/classes/UniversalAgent/instances/assistant/UserMessageEvent" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "blocks": [{"block_type": "text", "text": "What is the total due?"}]}],
    "files": [{"filename": "invoice.pdf", "file_type": "application/pdf", "content": "'"$(base64 -w0 invoice.pdf)"'"}]
  }'
```

A request is checked as a whole before any of its files is stored, so a rejected request leaves nothing behind:

| Rejected with | When                                                                                    |
| ------------- | --------------------------------------------------------------------------------------- |
| `413`         | A file exceeds `AGENT_INLINE_FILE_MAX_FILE_BYTES` (25 MB by default)                    |
| `413`         | A request carries more than `AGENT_INLINE_FILE_MAX_FILES_PER_REQUEST` (10) inline files |
| `413`         | A JSON body exceeds `API_REQUEST_MAX_JSON_BODY_BYTES` (64 MB), checked as it arrives    |
| `415`         | Agents cannot read the file type, or the file is an image (send images in the message)  |
| `422`         | The content is not valid base64                                                         |

Files sent inline never travel inside the event itself, which keeps events small enough for the message bus and the
event history. The [OpenAI-compatible API](../1_openai_compatible_api/) accepts files for agents the same way, as `file`
content parts.
