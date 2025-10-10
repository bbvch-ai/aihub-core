---
title: Agent Interaction REST API
index: 2
---

# Agent Interaction REST API

## Overview

The Agent Interaction REST API is the native HTTP interface designed specifically for managing and interacting with
AI-Hub's core capabilities: agents, threads (conversations), processes, and platform resources. Unlike the
OpenAI-Compatible API that provides a standardized LLM interface, this API exposes the full agent orchestration and
process automation functionality unique to the Swiss AI-Hub platform.

## Design Rationale

### Platform-Native Operations

While the OpenAI-Compatible API enables seamless migration for existing applications, the Agent Interaction API is
purpose-built for applications that want to leverage the full power of the Swiss AI-Hub's agent-based architecture. It
provides direct access to:

- Agent lifecycle management (discovery, configuration, execution)
- Conversational thread management with multi-agent collaboration
- Process orchestration and monitoring
- Event history and observability
- Resource and permission management

### Event-Driven Integration

The Agent Interaction API serves as the HTTP gateway to the platform's event-driven core. HTTP requests are translated
into NATS events that flow through the agent system, enabling:

- Asynchronous agent execution with synchronous HTTP responses
- Distributed agent processing across multiple service instances
- Event replay and debugging capabilities
- Comprehensive observability through structured event streams

## Core Capabilities

### 1. Agent Management

**Endpoints**:

- `GET /agents/` - List all available agents (online and offline)
- `GET /agents/discover` - Discover currently online agents
- `GET /agents/{agent_class}/{agent_id}` - Retrieve specific agent details
- `GET /agents/{agent_class}/{agent_id}/threads` - List threads for a specific agent

**Functionality**:

**Agent Discovery**: The platform broadcasts discovery requests via NATS, collecting responses from all active agent
services. This dynamic discovery mechanism ensures the API always reflects the current agent topology without requiring
static configuration.

**Agent Metadata**: Each agent provides rich metadata including:

- Descriptive information (name, description, icon)
- Configuration parameters and their types
- Capability declarations (supports streaming, multimodal inputs, etc.)
- Performance characteristics (typical response time, resource requirements)

**Access Control**: Agent listings are filtered based on user permissions, ensuring users only see agents they are
authorized to access. The hierarchical permission system supports both agent-class-level and instance-level access
control.

### 2. Thread (Conversation) Management

**Endpoints**:

- `GET /threads/` - List user's threads with pagination
- `POST /threads/` - Create a new thread
- `GET /threads/{thread_id}` - Retrieve thread details
- `PATCH /threads/{thread_id}` - Update thread metadata
- `DELETE /threads/{thread_id}` - Delete a thread
- `POST /threads/{thread_id}/agents` - Add an agent to a thread
- `POST /threads/{thread_id}/users` - Add a user to a thread
- `GET /threads/{thread_id}/messages` - Retrieve message history

**Functionality**:

**Thread Lifecycle**: Threads represent persistent conversations that can involve multiple users and agents. The API
manages the complete thread lifecycle from creation through archival or deletion.

**Multi-Agent Collaboration**: A single thread can include multiple agents with different specializations, enabling
complex workflows where agents collaborate to solve user problems. The API manages agent participation and message
routing within threads.

**Message History**: All interactions within a thread are persisted, enabling context reconstruction, conversation
replay for debugging, and compliance audit trails.

**Access Control**: Thread access is determined by:

- Direct user membership in the thread
- Ownership of the associated process (if thread is part of a process execution)
- Administrative permissions for platform operators

### 3. Process Management

**Endpoints**:

- `GET /processes/` - List user's processes
- `GET /processes/{process_class}/{process_id}` - Retrieve process details
- `POST /processes/{process_class}/{process_id}/start` - Initiate a process execution
- `GET /processes/{process_class}/{process_id}/runs` - List process execution history
- `GET /processes/{process_class}/{process_id}/runs/{run_id}` - Retrieve specific run details

**Functionality**:

**Process Orchestration**: Processes represent complex, multi-step workflows that may involve multiple agents, human
interactions, and external system integrations. The API provides endpoints to initiate, monitor, and control process
executions.

**Run Management**: Each process execution is tracked as a "run" with associated state, thread references, and outcome
tracking. This enables comprehensive process monitoring and debugging.

**Event Integration**: Process state changes are published as events, allowing real-time monitoring through the
WebSocket API and comprehensive observability through the event history endpoints.

### 4. Event History and Observability

**Endpoints**:

- `GET /events/agents/threads/{thread_id}` - Retrieve all events in a thread
- `GET /events/agents/timeseries/{time_range}` - Get time-series event statistics

**Functionality**:

**Event History**: All agent interactions, state changes, and system events are persisted, enabling:

- Debugging of agent behaviors and decision-making processes
- Compliance audit trails
- Performance analysis and optimization
- Conversation replay for testing and validation

**Time-Series Analytics**: The platform aggregates event data into time-series buckets, providing insights into:

- Agent usage patterns over time
- Performance trends and anomalies
- Resource utilization
- Error rates and failure modes

**Contextual Filtering**: Event queries can be filtered by thread, agent class, agent instance, or event type, enabling
targeted analysis and debugging.

### 5. User and Role Management

**Endpoints**:

- `GET /users/me` - Retrieve current user profile
- `GET /users/me/dashboard` - Get user's dashboard data (recent threads, favorite agents)
- `GET /roles/` - List available roles
- `POST /roles/` - Create a new role
- `PUT /roles/{role_id}` - Update role permissions

**Functionality**:

**User Profile Management**: Users can retrieve and update their profile information, preferences, and usage statistics.

**Role-Based Access Control**: The API enables administrators to define and manage roles with specific permission sets,
implementing fine-grained access control across platform resources.

**Dashboard Data**: Personalized dashboard endpoints provide users with quick access to their recent activities and
frequently used agents.

### 6. Knowledge Management

**Endpoints**:

- `GET /knowledge/` - List knowledge bases
- `POST /knowledge/` - Create knowledge base
- `GET /knowledge/{kb_id}/nodes` - Retrieve knowledge graph nodes
- `POST /knowledge/{kb_id}/ingest` - Trigger data ingestion

**Functionality**:

**Knowledge Base Management**: Create and configure knowledge bases that agents can use for retrieval-augmented
generation (RAG).

**Content Ingestion**: Trigger and monitor document ingestion pipelines that populate knowledge bases with
organization-specific information.

**Graph Exploration**: Query the knowledge graph structure, enabling advanced knowledge discovery and relationship
analysis.

### 7. Evaluation and Testing

**Endpoints**:

- `GET /evaluation/datasets` - List evaluation datasets
- `POST /evaluation/datasets` - Create dataset
- `POST /evaluation/experiments` - Run evaluation experiment
- `GET /evaluation/experiments/{experiment_id}/results` - Retrieve experiment results

**Functionality**:

**Dataset Management**: Create and manage test datasets for agent evaluation, enabling systematic quality assessment and
regression testing.

**Experiment Execution**: Run agents against test datasets, capturing performance metrics and comparing results across
different agent versions or configurations.

**Quality Metrics**: Automated calculation of quality metrics (accuracy, relevance, latency) for agent responses.

## Authentication and Access Control

OAuth2 bearer tokens validated against organizational identity providers provide authentication. Authorization uses
hierarchical permission patterns enabling fine-grained access control at both resource class and instance levels.
Dynamic permission evaluation occurs at runtime based on resource ownership and user roles, with support for wildcard
permissions for administrative access.

## Integration and Usage Patterns

The API serves as the primary interface for native AI-Hub applications, providing RESTful access to all platform
capabilities. List endpoints include pagination support for efficient handling of large result sets. Standard HTTP
status codes and structured error responses ensure consistent error handling. Query parameters enable filtering and
sorting across endpoints for targeted resource retrieval.

**Key Integration Scenarios**:

- Native application development leveraging full platform capabilities
- Real-time monitoring through combined REST and WebSocket usage
- Administrative automation and custom tooling development
- Cross-origin web application integration via CORS support

## Architecture and Observability

The API operates as part of the main platform service with stateless design enabling horizontal scaling. All requests
are instrumented via OpenTelemetry for distributed tracing across HTTP and NATS boundaries. Structured logging captures
contextual information for all operations, with HTTP requests correlated to resulting platform events and agent
executions. Efficient connection pooling and TTL-based caching optimize resource utilization.
