---
title: OpenAI-Compatible REST API
index: 1
---

# OpenAI-Compatible REST API

## Overview

The OpenAI-Compatible REST API provides a standards-based HTTP interface that mirrors the OpenAI API specification,
enabling seamless integration for applications and tools built on OpenAI SDKs. This API serves as a drop-in replacement
for OpenAI endpoints, allowing organizations to leverage Swiss AI-Hub infrastructure while maintaining full
compatibility with existing codebases.

## Design Rationale

### API Compatibility Strategy

The controller is designed to mirror the exact API interface provided by OpenAI, ensuring that customers can seamlessly
switch from OpenAI's services to the Swiss AI-Hub without modifying their client code. Every endpoint that OpenAI
offers—ranging from model management, chat completions, embeddings, image generation, to audio processing (both
speech-to-text and text-to-speech)—is implemented with the same request/response structure expected by the OpenAI Python
and JavaScript SDKs.

### Vendor-Neutral Model Access

The API abstracts underlying model providers, supporting multiple LLM configurations including Azure OpenAI, self-hosted
models, and other OpenAI-compatible services. This vendor neutrality enables organizations to:

- Switch between model providers without application changes
- Implement cost optimization strategies across multiple vendors
- Maintain data sovereignty through self-hosted model options
- Leverage hybrid deployment models (cloud + on-premise)

### Extension: AI-Hub Assistants as Models

Beyond standard LLM models, the Swiss AI-Hub extends the OpenAI model concept to include AI-Hub assistants (agents).
Assistants are exposed as specialized "models" with names following the pattern `{agent_class}/{agent_id}`, enabling
applications to interact with complex agent workflows using the same familiar chat completion interface.

## Core Capabilities

### 1. Model Management

**Endpoints**:

- `GET /openai/models` - List available models and assistants
- `GET /openai/models/{model_name}` - Retrieve specific model details

**Functionality**:

- Discovery of available LLM models configured in the platform
- Optional inclusion of AI-Hub assistants as conversational models
- Model metadata including provider, capabilities, and configuration
- Access control filtering based on user permissions

### 2. Chat Completions

**Endpoints**:

- `POST /openai/chat/completions` - Create chat completion

**Functionality**:

- Synchronous and streaming response modes
- Support for both standard LLM models and AI-Hub assistants
- Full message history context
- Function calling and tool use capabilities (when supported by underlying model)
- Multimodal inputs (text, images) for vision-capable models

**Key Features**:

- Streaming responses for progressive UI updates using Server-Sent Events (SSE)
- Automatic routing to appropriate backend (LLM proxy vs. agent system)
- Context preservation across multi-turn conversations
- User identity propagation for access control and observability

### 3. Embeddings

**Endpoints**:

- `POST /openai/embeddings` - Create embedding vectors

**Functionality**:

- Text-to-vector conversion for semantic search and retrieval
- Support for multiple embedding models and dimensions
- Batch processing for multiple input texts
- Configurable output encoding formats

### 4. Image Generation

**Endpoints**:

- `POST /openai/images/generations` - Generate images from text prompts

**Functionality**:

- Text-to-image generation using DALL-E or compatible models
- Configurable image sizes and quality levels
- Multiple output format support
- Prompt engineering and style controls

### 5. Audio Processing

#### Speech-to-Text (Transcription)

**Endpoints**:

- `POST /openai/audio/transcriptions` - Transcribe audio to text

**Functionality**:

- Audio file transcription with multiple format support (MP3, WAV, M4A, etc.)
- Language detection or explicit language specification
- Optional timestamp granularity (word-level or segment-level)
- Transcript formatting options (JSON, text, SRT, VTT)

#### Text-to-Speech (TTS)

**Endpoints**:

- `POST /openai/audio/speech` - Generate speech from text

**Functionality**:

- Text-to-speech conversion with multiple voice options
- Streaming audio output for real-time playback
- Configurable audio format and quality
- Speed and prosody controls

## Integration Approach

The API provides drop-in compatibility with OpenAI SDKs, requiring only base URL and authentication token changes.
Organizations can seamlessly mix standard LLM models with AI-Hub assistants within the same application, enabling
gradual migration strategies.

**Key Integration Benefits**:

- Existing OpenAI-based applications work without code changes
- Unified interface for both external LLMs and platform-native agents
- Streaming support for real-time user interfaces
- Transparent routing between model providers and agent workflows

## Security and Access Control

Authentication and authorization are enforced through the platform's unified security layer using OAuth2 bearer tokens
validated against organizational identity providers. Hierarchical permission checks control access to both LLM models
and AI-Hub assistants, with all operations tracked for observability and cost attribution.

## Architecture Characteristics

The API operates as part of the main platform service with stateless design enabling horizontal scaling. Request routing
logic transparently directs standard model requests to the LLM proxy layer while converting assistant requests into
platform events for agent processing. Comprehensive instrumentation via OpenTelemetry provides end-to-end tracing and
performance monitoring.
