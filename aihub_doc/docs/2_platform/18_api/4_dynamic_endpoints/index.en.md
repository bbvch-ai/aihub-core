---
title: Dynamic Agent and Process Endpoints
---

# Dynamic Agent and Process Endpoints :rocket: :100:

::: info **TL;DR - What are Dynamic Endpoints?**
The AI-Hub automatically creates REST API endpoints on-the-fly based on the agents and processes available in your
system. When a new agent or process comes online, the API gateway instantly generates custom endpoints tailored to that
specific component's capabilities, eliminating the need for manual API development and ensuring your system stays
perfectly synchronized.
:::

## What are Dynamic Endpoints and How Do They Work? :brain:

Dynamic Agent and Process Endpoints represent a revolutionary approach to API generation in distributed AI systems.
Instead of pre-defining static API routes, the AI-Hub employs **intelligent endpoint discovery services** that:

- **Continuously scan** the NATS message bus for available agents and processes
- **Automatically generate** REST endpoints based on each component's event specifications
- **Dynamically register** these endpoints with the FastAPI application at runtime
- **Maintain synchronization** between your running services and available API endpoints

This system leverages two core discovery services:

- **`AgentEndpointsDiscoveryService`**: Creates endpoints like `/agents/{agent_class}/{agent_id}/{event_name}` for
  sending events to specific agents
- **`ProcessEndpointsDiscoveryService`**: Generates endpoints like `/processes/{process_class}/{process_id}/{route}` for
  human and program interaction with processes

The discovery process uses **NATS-based service discovery** to query running components about their capabilities, then
uses the **Jambo SchemaConverter** to transform event schemas into Pydantic models that power fully-typed, documented
API endpoints.

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

Dynamic endpoints are enabled automatically when you start the AI-Hub with the full infrastructure stack:

1. **NATS Message Bus**: Required for service discovery communication
2. **API Gateway**: The `aihub_api` service with `lifetime_manager` enabled
3. **Discovery Services**: Automatically started by the lifetime manager

## Agent Endpoint Generation

For each discovered agent, the system creates endpoints following this pattern:

```
POST /api/v1/agents/{agent_class}/{agent_id}/{event_name}
```

**Example**: An agent with class `rag_agent` and ID `customer_support` that accepts `UserMessageEvent` would get:

```
POST /api/v1/agents/rag_agent/customer_support/user_message_event
```

## Process Endpoint Generation

For each discovered process, the system creates endpoints based on the process definition:

```
GET  /api/v1/processes/{process_class}/{process_id}/{route}         # Get form
POST /api/v1/processes/{process_class}/{process_id}/{route}         # Submit form
GET  /api/v1/processes/{process_class}/{process_id}/{walkthrough_id}/{route}  # Continue process
POST /api/v1/processes/{process_class}/{process_id}/{walkthrough_id}/{route}  # Submit continuation
```

## Available Capabilities

Dynamic endpoints provide:

- **Full OpenAPI Documentation**: Every endpoint appears in `/docs` with complete request/response schemas
- **Type Validation**: Automatic request validation based on event specifications
- **Authentication**: Inherited from the base controller security model
- **Error Handling**: Standardized error responses and HTTP status codes
- **Caching**: Built-in response caching for discovery-related operations

## Security and Best Practices

**Access Control**:

- Agent endpoints require `aihub.user.agent.{agent_class}.{agent_id}` permission
- Process endpoints require `aihub.user.process.{process_class}.{process_id}` permission

**Rate Limiting**: Discovery services run on configurable intervals (default: 60 seconds) to balance responsiveness with
system load

**Monitoring**: All dynamic endpoint usage is logged and traced through standard AI-Hub observability tools

**Performance**: Dynamic endpoints are cached and only regenerated when the system topology changes
:::

## Getting Started

To begin using dynamic endpoints in your AI-Hub:

1. **Start the Infrastructure**: Ensure NATS and the API gateway are running with the standard Docker Compose setup
2. **Deploy Agents/Processes**: Any agent or process that connects to NATS will automatically get endpoints
3. **Discover Endpoints**: Check `/api/v1/docs` to see all dynamically generated endpoints
4. **Integrate**: Use the standard REST endpoints to integrate with external systems or build custom frontends

The dynamic endpoint system transforms the AI-Hub from a static API into a living, adaptive integration layer that grows
with your AI capabilities.
