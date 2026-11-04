---
title: API
---

# OpenAI-Compatible REST API

## Concept and Purpose

The OpenAI-Compatible REST API provides a standards-based HTTP interface built on FastAPI that follows the OpenAI API
specification. Applications built on the OpenAI SDKs call language models on the Swiss AI Hub by changing only the API
endpoint URL and the authentication token. Agents are called through the same interface; how much of the OpenAI request
they honour is described in [Calling Agents](#calling-agents).

The strategic value of this compatibility layer lies in reducing migration friction and protecting existing technology
investments. Organizations can adopt Swiss AI Hub infrastructure for data sovereignty, cost control, or compliance
reasons while preserving their application ecosystem built on OpenAI SDKs and libraries.

## Core Design Principles

### Seamless Migration and Integration

The API covers the major OpenAI capabilities: conversational AI (chat completions), semantic search (embeddings), image
generation, and audio processing (speech-to-text and text-to-speech). Requests to language models are forwarded to the
model gateway with their parameters, so applications developed with OpenAI's Python or JavaScript SDKs keep working,
within what the configured model supports.

Responses follow the OpenAI formats, including server-sent events ending in `data: [DONE]` for streamed chat
completions. Every error carries OpenAI's `error` object (`message`, `type`, `param`, `code`), whether the model gateway
or the platform raised it, and a request the API cannot accept is a `400`. A `detail` field with the same content stays
next to it for the platform's own clients.

### Vendor-Neutral Model Access

The API abstracts underlying model providers, supporting multiple LLM sources including Swiss LLM Cloud, self-hosted
vLLM models, and other OpenAI-compatible services. This vendor neutrality provides several business advantages:
organizations can switch between model providers transparently without application changes, implement cost optimization
strategies by routing requests to different vendors based on workload characteristics, maintain data sovereignty through
self-hosted model options, and leverage hybrid deployment models combining cloud and on-premise resources.

Model selection and routing occur transparently at the platform level, allowing centralized governance and optimization
without requiring coordination across application teams.

### Extended Model Concept: Swiss AI Hub Assistants

Beyond standard language models, the Swiss AI Hub extends the OpenAI model concept to include platform-native AI
assistants (agents). These assistants appear as specialized models alongside traditional LLMs, enabling applications to
interact with complex, stateful agent workflows using the same familiar chat interface.

This extension provides a migration path for organizations seeking to evolve from simple LLM interactions toward
orchestrated agent workflows. Applications can start by calling basic language models and progressively adopt more
sophisticated agents without architectural changes - the same API interface serves both use cases.

## Supported Capabilities

The API provides full-spectrum AI functionality compatible with modern LLM applications:

**Conversational AI**: Chat completions with both synchronous and streaming response modes, enabling interactive
applications and progressive UI updates. For language models the interface supports multi-turn conversations, function
calling and multimodal inputs (text and images) for vision-capable models. Agents additionally accept documents as
`file` content parts.

**Semantic Search**: Embedding generation converts text into vector representations for semantic search, similarity
matching, and retrieval-augmented generation workflows. This capability supports batch processing and multiple embedding
model configurations.

**Multimodal Generation**: Image generation from text prompts and audio processing capabilities including speech-to-text
transcription (supporting multiple audio formats and languages) and text-to-speech synthesis with configurable voices
and streaming output.

**Model Discovery**: The model listing returns the language models a user may access, and with `?include_agents=true`
also the agents they may call, under their ids (`AgentClass/agent_id`). Agents are left out by default because OpenWebUI
lists this endpoint and shows agents through its own pipe.

## Business Value

### Reduced Migration Risk and Cost

Organizations can adopt the Swiss AI Hub platform without rewriting applications, eliminating migration project costs
and reducing adoption risk. Existing development teams continue using familiar OpenAI SDKs and patterns, avoiding
retraining overhead. This compatibility preserves investments in application code, testing infrastructure, and
operational runbooks.

### Centralized Governance and Cost Control

The compatibility layer provides a single control point for model access across the organization. Platform
administrators can implement cost controls, usage quotas, and routing policies without requiring changes to individual
applications. Model provider switching occurs transparently, enabling cost optimization and avoiding vendor lock-in.

### Progressive Enhancement Path

The unified interface between basic LLM models and sophisticated AI assistants enables organizations to evolve their AI
capabilities incrementally. Applications built for simple model access can progressively adopt more advanced agent-based
workflows as organizational maturity increases, without requiring architectural redesign.

## Implementation Approach

Built on FastAPI, the API operates as part of the main platform service with stateless request handling enabling
horizontal scaling. Authentication integrates with organizational identity providers via OAuth2, and hierarchical
permissions control access to both LLM models and AI assistants. Request routing logic transparently directs model
requests to the LLM proxy layer while converting assistant interactions into platform events for agent processing,
maintaining clean separation between external model access and internal agent orchestration.

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

The Swiss AI Hub platform exposes multiple API types, each optimized for specific interaction patterns and use cases:

### 1. OpenAI-Compatible REST API

A standards-based HTTP API following OpenAI's API specification, so applications built on OpenAI SDKs reach language
models on the Swiss AI Hub by changing the endpoint URL and token. The API supports chat completions, embeddings, image
generation, and audio processing (speech-to-text and text-to-speech) with OpenAI's endpoint structures and
request/response formats. Agents are called through the same chat completions endpoint, in streaming and non-streaming
mode; see [Calling Agents](./1_openai_compatible_api/#calling-agents) for what they accept.

### 2. Agent Interaction REST API

A native HTTP API designed specifically for managing and interacting with AI agents, threads (conversations), processes,
and platform resources. This API provides comprehensive access to the platform's full capabilities, including agent
discovery and configuration, conversation lifecycle management, process execution and monitoring, event history access,
and user/role administration. It is optimized for building native Swiss AI Hub applications that leverage the platform's
complete agent orchestration and process automation features.

### 3. WebSocket API

A bidirectional, real-time communication channel enabling live event streaming and continuous updates for interactive
applications. The WebSocket API delivers agent events, status updates, and streaming responses as they occur with low
latency, supporting progressive display of agent responses in user interfaces. It provides connection-based session
management with token-based authentication and automatic disconnection on authorization failure. This API is optimized
for real-time user interfaces requiring immediate feedback and live updates during agent execution.

### 4. Model Context Protocol (MCP) Server

An HTTP-based MCP server that exposes Swiss AI Hub API endpoints as resources and tools accessible to AI development
assistants and automation tools. This enables AI coding assistants like Claude Code and Gemini CLI to query platform
state, inspect agents, and interact with the Swiss AI Hub API during development sessions. The server provides automatic
resource and tool discovery from API endpoints, read-only access to GET endpoints as MCP resources, and dynamic schema
generation from OpenAPI specifications.
