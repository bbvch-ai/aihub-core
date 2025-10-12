---
title: APIs
index: 1
---

# APIs

![System Overview - APIs](../../../../../../media/architecture/system_overview/system-overview-highlight-api.png)

The API layer serves as the central gateway for all external interactions with the Swiss AI-Hub platform. It provides
secure, standards-based interfaces for user applications, administrative tools, and integration endpoints.

## Purpose and Scope

The API component encompasses all programmatic interfaces that allow external systems and users to interact with the
platform. This includes REST APIs for synchronous operations, WebSocket connections for real-time communication, and
specialized endpoints for authentication, authorization, and resource management.

## Key Responsibilities

**Authentication and Authorization**: The API layer enforces security boundaries, validating user identities through
integration with organizational identity providers (OAuth2, OIDC) and enforcing role-based access control policies.

**Request Routing**: Incoming requests are validated, authenticated, and routed to appropriate backend services. The API
acts as a facade, abstracting the complexity of the distributed service architecture from clients.

**Protocol Translation**: The API translates between external protocols (HTTP/REST, WebSocket) and internal event-driven
communication patterns, bridging synchronous client expectations with asynchronous backend processing.

**Session Management**: For conversational interfaces, the API maintains session context, managing long-lived
connections and ensuring state consistency across multiple interactions.

## API Types and Interfaces

The Swiss AI-Hub platform exposes multiple API types, each optimized for specific interaction patterns and use cases:

### 1. OpenAI-Compatible REST API

A standards-based HTTP API providing full compatibility with OpenAI's API specification, enabling seamless migration for
applications built on OpenAI SDKs. The API supports chat completions, embeddings, image generation, and audio processing
(speech-to-text and text-to-speech) with identical endpoint structures and request/response formats. This serves as a
drop-in replacement for OpenAI endpoints, allowing existing applications to leverage Swiss AI-Hub infrastructure without
code changes. The API supports both direct LLM model access and AI-Hub assistants (agents), with both streaming and
non-streaming modes for all capabilities.

### 2. Agent Interaction REST API

A native HTTP API designed specifically for managing and interacting with AI agents, threads (conversations), processes,
and platform resources. This API provides comprehensive access to the platform's full capabilities, including agent
discovery and configuration, conversation lifecycle management, process execution and monitoring, event history access,
and user/role administration. It is optimized for building native AI-Hub applications that leverage the platform's
complete agent orchestration and process automation features.

### 3. WebSocket API

A bidirectional, real-time communication channel enabling live event streaming and continuous updates for interactive
applications. The WebSocket API delivers agent events, status updates, and streaming responses as they occur with low
latency, supporting progressive display of agent responses in user interfaces. It provides connection-based session
management with token-based authentication and automatic disconnection on authorization failure. This API is optimized
for real-time user interfaces requiring immediate feedback and live updates during agent execution.

### 4. Model Context Protocol (MCP) Server

An HTTP-based MCP server that exposes AI-Hub API endpoints as resources and tools accessible to AI development
assistants and automation tools. This enables AI coding assistants like Claude Code and Gemini CLI to query platform
state, inspect agents, and interact with the AI-Hub API during development sessions. The server provides automatic
resource and tool discovery from API endpoints, read-only access to GET endpoints as MCP resources, and dynamic schema
generation from OpenAPI specifications.

### 5. Bot Framework API (Independent Component)

A separate, independently deployable service that integrates with Microsoft Azure Bot Service, enabling AI agents to
interact with users through familiar collaboration platforms like Microsoft Teams and Slack. This component translates
bot platform messages into AI-Hub events and streams agent responses back to users, bringing AI agents directly into
existing team collaboration workflows without requiring users to switch applications. The Bot API supports multi-channel
integration (Teams, Slack, Web Chat), stateful conversation tracking with configurable TTL, both streaming and
non-streaming response modes, and the Bot-in-the-Loop pattern for human collaboration within agent workflows. It is
packaged as a separate Docker container that connects to the AI-Hub event system via NATS messaging, maintaining loose
coupling while enabling seamless cross-platform agent interactions.
