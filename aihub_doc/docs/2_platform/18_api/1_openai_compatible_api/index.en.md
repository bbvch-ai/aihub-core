---
title: OpenAI-Compatible REST API
---

# OpenAI-Compatible REST API

## Concept and Purpose

The OpenAI-Compatible REST API provides a standards-based HTTP interface built on FastAPI that mirrors the OpenAI API
specification exactly. This design enables organizations to migrate existing AI-powered applications to the Swiss AI-Hub
platform without modifying application code—only the API endpoint URL and authentication token need to change.

The strategic value of this compatibility layer lies in reducing migration friction and protecting existing technology
investments. Organizations can adopt Swiss AI-Hub infrastructure for data sovereignty, cost control, or compliance
reasons while preserving their application ecosystem built on OpenAI SDKs and libraries.

## Core Design Principles

### Seamless Migration and Integration

The API implements complete compatibility with OpenAI's interface, supporting all major capabilities including
conversational AI (chat completions), semantic search (embeddings), image generation, and audio processing
(speech-to-text and text-to-speech). Applications developed using OpenAI's Python or JavaScript SDKs function without
modification, enabling rapid platform adoption and reducing implementation risk.

This compatibility extends to both request and response formats, streaming behaviors, and error handling patterns.
Organizations can validate the platform using existing test suites and migration scripts, accelerating evaluation and
deployment timelines.

### Vendor-Neutral Model Access

The API abstracts underlying model providers, supporting multiple LLM sources including Swiss LLM Cloud, self-hosted
vLLM models, and other OpenAI-compatible services. This vendor neutrality provides several business advantages:
organizations can switch between model providers transparently without application changes, implement cost optimization
strategies by routing requests to different vendors based on workload characteristics, maintain data sovereignty through
self-hosted model options, and leverage hybrid deployment models combining cloud and on-premise resources.

Model selection and routing occur transparently at the platform level, allowing centralized governance and optimization
without requiring coordination across application teams.

### Extended Model Concept: AI-Hub Assistants

Beyond standard language models, the Swiss AI-Hub extends the OpenAI model concept to include platform-native AI
assistants (agents). These assistants appear as specialized models alongside traditional LLMs, enabling applications to
interact with complex, stateful agent workflows using the same familiar chat interface.

This extension provides a migration path for organizations seeking to evolve from simple LLM interactions toward
orchestrated agent workflows. Applications can start by calling basic language models and progressively adopt more
sophisticated agents without architectural changes—the same API interface serves both use cases.

## Supported Capabilities

The API provides full-spectrum AI functionality compatible with modern LLM applications:

**Conversational AI**: Complete chat completion support with both synchronous and streaming response modes, enabling
interactive applications and progressive UI updates. The interface supports multi-turn conversations, function calling,
and multimodal inputs (text and images) for vision-capable models.

**Semantic Search**: Embedding generation converts text into vector representations for semantic search, similarity
matching, and retrieval-augmented generation workflows. This capability supports batch processing and multiple embedding
model configurations.

**Multimodal Generation**: Image generation from text prompts and audio processing capabilities including speech-to-text
transcription (supporting multiple audio formats and languages) and text-to-speech synthesis with configurable voices
and streaming output.

**Model Discovery**: Dynamic model listing enables applications to discover available LLM models and AI-Hub assistants
at runtime, supporting adaptive interfaces and centralized model governance.

## Business Value

### Reduced Migration Risk and Cost

Organizations can adopt the Swiss AI-Hub platform without rewriting applications, eliminating migration project costs
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
