---
title: Model Context Protocol (MCP) Server
index: 4
---

# Model Context Protocol (MCP) Server

## Overview

The Model Context Protocol (MCP) Server exposes Swiss AI-Hub API endpoints as resources and tools accessible to AI
development assistants and automation tools. This specialized interface enables AI coding assistants like Claude Code,
Gemini CLI, and other MCP-compatible tools to interact directly with the platform during development workflows,
providing real-time access to platform state, agent configurations, and operational data.

## Design Rationale

### AI-Assisted Development Integration

Modern software development increasingly leverages AI coding assistants for tasks like debugging, testing, code
generation, and documentation. These assistants are most effective when they have direct access to the systems they're
helping to develop. The MCP Server bridges this gap by:

- **Providing Real-Time Context**: AI assistants can query current platform state, agent configurations, and execution
  histories
- **Enabling Interactive Debugging**: Assistants can inspect running agents, trace event flows, and analyze errors
- **Supporting Automated Testing**: Tools can discover agents, execute test scenarios, and validate behaviors
- **Facilitating Documentation**: Assistants can extract API schemas, agent metadata, and usage patterns for
  documentation generation

### Model Context Protocol Standards

MCP is an emerging standard for exposing application functionality to AI assistants in a structured, discoverable way.
By implementing an MCP server, the Swiss AI-Hub:

- **Ensures Compatibility**: Works with any MCP-compatible AI assistant or automation tool
- **Enables Future Integration**: As MCP adoption grows, new tools automatically gain access
- **Provides Type Safety**: MCP's schema-based approach ensures correct tool usage by AI assistants
- **Supports Discovery**: AI assistants can automatically discover available resources and tools without hardcoded
  knowledge

### Automatic API Translation

The MCP Server automatically translates the existing REST API into MCP resources and tools:

- **No Duplicate Implementation**: The same FastAPI endpoints serve both human developers and AI assistants
- **Automatic Schema Generation**: OpenAPI specifications are converted to MCP schemas
- **Consistent Behavior**: MCP tools invoke the same business logic as REST endpoints, ensuring consistency
- **Reduced Maintenance**: Changes to the REST API automatically reflect in the MCP interface

## Core Capabilities

### 1. Resource Discovery and Access

MCP exposes HTTP GET endpoints as "resources" that AI assistants can read to gather information:

**Resource Types**:

**Agent Resources**:

- `aihub://agents/` - List of all agents
- `aihub://agents/discover` - Currently online agents
- `aihub://agents/{agent_class}/{agent_id}` - Specific agent details
- `aihub://agents/{agent_class}/{agent_id}/threads` - Threads for a specific agent

**Thread Resources**:

- `aihub://threads/` - User's conversation threads
- `aihub://threads/{thread_id}` - Specific thread details
- `aihub://threads/{thread_id}/messages` - Message history for a thread

**Event Resources**:

- `aihub://events/agents/threads/{thread_id}` - Events in a thread
- `aihub://events/agents/timeseries/{time_range}` - Time-series event statistics

**Process Resources**:

- `aihub://processes/` - Available processes
- `aihub://processes/{process_class}/{process_id}` - Specific process details

**Resource Templates**: Resources with path parameters (e.g., `{thread_id}`) are exposed as "resource templates" in MCP,
enabling AI assistants to dynamically construct resource URIs based on context.

### 2. Tool Generation (Future Capability)

While the current implementation focuses on read-only resources (GET endpoints), the architecture supports future
expansion to expose POST, PUT, PATCH, and DELETE endpoints as MCP "tools":

**Potential Future Tools**:

- `create_thread` - Create a new conversation thread
- `send_message` - Send a message to an agent
- `start_process` - Initiate a process execution
- `add_agent_to_thread` - Add an agent to a conversation

**Security Considerations for Tools**: Write operations through MCP require careful consideration:

- **User Consent**: AI assistants must obtain explicit user approval for state-changing operations
- **Access Control**: Tools must enforce the same permission checks as REST endpoints
- **Audit Logging**: All tool invocations are logged with user context for compliance

Currently, tools are **excluded** from the MCP server to maintain a read-only development interface, reducing security
risks.

### 3. Dynamic Schema Generation

The MCP Server automatically generates schemas for all exposed resources:

**OpenAPI to MCP Translation**: FastAPI's OpenAPI specification (generated from code annotations) is transformed into
MCP resource and tool schemas. This ensures:

- **Type Safety**: AI assistants understand expected response structures
- **Validation**: Responses are validated against schemas before delivery
- **Documentation**: AI assistants have access to human-readable descriptions from OpenAPI

OpenAPI specifications are automatically transformed into MCP resource schemas, providing type safety, response
validation, and human-readable descriptions to AI assistants.

## Implementation Architecture

The MCP server is generated from the existing FastAPI application using the FastMCP library. HTTP GET endpoints are
categorized as MCP resources (static or templates based on path parameters), while write operations (POST, PUT, PATCH,
DELETE) are excluded for security. The server is mounted at `/mcp` on the main API service, sharing the same lifecycle,
authentication infrastructure, and connection resources.

## Authentication and Security

Bearer token authentication using the same OAuth2/SAML/LDAP identity providers as REST endpoints ensures consistent
access control. Resources are filtered based on user permissions, preventing AI assistants from accessing unauthorized
data (agents, threads, events, processes). AI coding assistants configure MCP connections via `.mcp.json` configuration
files with automated token refresh flows.

## Use Cases

The MCP Server enables four primary development workflows:

**AI-Assisted Debugging**: Developers query real-time platform state through conversational interfaces, eliminating
manual API exploration.

**Automated Testing**: AI assistants validate agent behavior by inspecting execution histories and analyzing event
streams.

**Documentation Generation**: Assistants extract live platform data and schemas to generate current, accurate
documentation.

**Interactive Development**: Developers receive AI-generated code validated against actual API schemas, accelerating
application development.

## Security and Access Model

The implementation is **read-only by default**, exposing only GET endpoints to reduce risk and enable safe exploration.
Write operations are excluded, eliminating needs for complex approval workflows. Hierarchical permission checks ensure
AI assistants respect user access boundaries. All MCP resource access is instrumented for security monitoring and
anomaly detection.

## Architecture Characteristics

The MCP server is embedded within the main API service, requiring no separate deployment. It shares authentication,
database connections, and NATS clients with REST endpoints, scaling horizontally with API instances. Standard HTTP load
balancing applies, with schemas cached to optimize performance. Typical latency matches underlying REST endpoints
(100-500ms), with minimal CPU and memory overhead.
