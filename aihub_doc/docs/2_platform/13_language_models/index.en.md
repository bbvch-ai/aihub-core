---
title: Language models
index: 13
---

# Language models

The AI-Hub integrates with language model providers through LiteLLM, a unified gateway that handles routing, cost
tracking, and security. Agents access models through this proxy layer without needing provider-specific code.

## Supported models

LiteLLM supports 100+ LLM providers including OpenAI, Azure OpenAI, Anthropic, Google, AWS Bedrock, and others. The
platform can integrate with any provider LiteLLM supports.

Currently configured providers:

- Azure OpenAI models
- Google Gemini models
- Self-hosted models via llama.cpp or Hugging Face Text Embedding Inference
- Any OpenAI-compatible API endpoint

Models are configured in LiteLLM with metadata about capabilities (chat, embedding, vision, function calling), token
limits, and costs. Agents specify which model to use in their configuration. Adding new providers requires updating the
LiteLLM configuration file.

## Architecture

The platform uses three layers:

LLM proxy layer: Provides a unified gateway to language model providers. See [Proxy server](./1_proxy_server/) for
routing, cost tracking, and retry handling.

Agent layer: Agents implement workflows using LLMs through the proxy. See [Guards](./3_guards/) for input and output
validation.

User layer: Users interact with agents through chat interfaces.

## How the layers work together

When a user asks a question:

1. The question reaches the agent
2. Agent input guards (optional) validate the question is appropriate
3. Presidio (if enabled) scans for PII in the question at the proxy layer
4. The proxy routes the request to the configured LLM provider
5. The LLM generates a response
6. Agent output guards (optional) check response quality and redact PII from retrieved documents
7. The response reaches the user

This layered approach provides defense-in-depth for both functionality (guards ensure quality) and security (Presidio
protects user input, output guards protect retrieved data).

## Components

- [Proxy server](./1_proxy_server/): LiteLLM configuration, routing, and cost tracking
- [Data anonymization](./2_anonymization/): Presidio integration for PII protection in user input
- [Guards](./3_guards/): Agent-level input and output validation for quality and security
