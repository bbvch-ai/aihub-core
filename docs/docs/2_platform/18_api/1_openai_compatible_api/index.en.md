---
title: OpenAI-Compatible REST API
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

## Calling Agents

An agent is called like a model, on the chat completions endpoint, with its class and instance as the model id:

```python
from openai import OpenAI

client = OpenAI(base_url="https://<host>/api/v1/active/openai", api_key="<token>")
response = client.chat.completions.create(
    model="UniversalAgent/assistant",
    messages=[{"role": "user", "content": "What is the total due?"}],
)
```

The messages become a user message to the agent, which decides how to answer: it may search knowledge, call tools or ask
a question back. Because of that, an agent call honours less of the request than a model call does.

**Content parts**

| Part          | Agents                                                                                                                          |
| ------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| `text`        | Passed to the agent                                                                                                             |
| `image_url`   | Passed to the agent, which shows it to its model if that model accepts images; images sent as data are stored first (see below) |
| `file`        | Stored and attached to the agent's run, from the last user message (see below)                                                  |
| `input_audio` | Refused with `400`: transcribe the audio with `/audio/transcriptions` and send the text                                         |

**Files.** A `file` part sends a document with the question, the way the OpenAI SDKs attach PDFs:

```python
content = [
    {"type": "text", "text": "What is the total due?"},
    {"type": "file", "file": {"filename": "invoice.pdf", "file_data": f"data:application/pdf;base64,{pdf_base64}"}},
]
```

`file_data` is the content encoded as base64, as a `data:` URL or plain (the type is then taken from the filename). Only
the files of the last user message are attached: earlier messages are history, whose files were attached on their own
turn. References to files hosted by OpenAI (`file_id`) are refused. The limits and errors are the same as for the
[agent endpoints](../4_dynamic_endpoints/#sending-files-to-an-agent): 25 MB per file and 10 files per request by
default, `413` above them, `415` for types agents cannot read and for images (send those as `image_url`), and nothing is
stored when a request is refused. A JSON request body may not exceed 64 MB.

**Images.** An `image_url` holding a `data:` URL is stored in the agent's file bucket, and the agent receives a
reference in the image's place, which it turns into a URL its model can read when it calls it. Images of any message
count, since a client without `reconstruct_history` sends the whole conversation each turn; an image sent again is
stored once. An image must be PNG, JPEG, GIF or WebP and may have 5 MB (`AGENT_INLINE_IMAGE_MAX_BYTES`), a larger one is
refused with `413`. Links to images on the web are passed on as they are.

**Parameters.** Agents choose their own model and its settings, so `temperature`, `top_p`, `max_tokens`, `stop`, `seed`,
`n` and `logprobs` have no effect on an agent call. Structured output through `response_format`, `tools` and
`tool_choice` is not supported by agents yet and is ignored too. The answer ends with `finish_reason: "stop"` and names
the agent (`AgentClass/agent_id`) as its `model`.

**Streaming.** A streamed answer is a sequence of `chat.completion.chunk` events with one id, the agent's id as `model`,
the role on the first chunk only, and `data: [DONE]` at the end. With `stream_options.include_usage`, a last chunk
without choices reports the tokens the agent used. An agent that fails during a streamed answer ends the stream with an
`error` event, which the OpenAI SDKs raise as an error.

**Platform extensions.** The `metadata` object of the request carries options OpenAI does not have:

| Field                 | Effect                                                                                                   |
| --------------------- | -------------------------------------------------------------------------------------------------------- |
| `thread_id`           | Continues the conversation in this thread, or starts one with this id                                    |
| `display_id`          | Sets the id the run is displayed under                                                                   |
| `reconstruct_history` | With `thread_id`: the agent gets the thread's stored history plus your last message, not your `messages` |
| `files`               | Files uploaded beforehand through the agent's upload endpoints, attached like `file` parts               |
| `features`            | Features the user asked for, such as `web_search`; the agent serves those it supports                    |

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
