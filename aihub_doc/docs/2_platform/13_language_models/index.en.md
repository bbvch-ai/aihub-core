---
title: Language models
index: 13
---

# Language models

The AI-Hub integrates with multiple language model providers through a centralized architecture. This section covers how
the platform manages LLM access, protects sensitive data, and ensures response quality.

## Architecture overview

The platform uses three layers for language model interactions:

**LLM proxy layer**: LiteLLM provides a unified gateway to all model providers (OpenAI, Google, Anthropic, Azure OpenAI,
self-hosted models). The proxy handles routing, cost tracking, retry logic, and platform-level PII protection via
Presidio.

**Agent layer**: Individual agents implement their workflows using LLMs through the proxy. Agents can enable input and
output guards to validate questions and responses specific to their purpose.

**User layer**: Users interact with agents through chat interfaces. The system tracks costs per conversation and applies
security controls transparently.

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

- **[Proxy server](./1_proxy_server/)**: LiteLLM configuration, routing, and cost tracking
- **[Data anonymization](./2_anonymization/)**: Presidio integration for PII protection in user input
- **[Guards](./3_guards/)**: Agent-level input and output validation for quality and security
