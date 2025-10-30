---
title: Proxy server
index: 1
---

# LLM proxy

The LLM proxy (LiteLLM) provides a centralized gateway to language model providers. It abstracts vendor-specific APIs behind an OpenAI-compatible interface, allowing the platform to work with multiple AI providers without changing code.

## What the proxy does

The proxy layer lets you change models through configuration files instead of modifying code. When you need to switch from one provider to another, update the configuration and restart the service.

## Core functions

**Unified interface**

LiteLLM provides an OpenAI-compatible API that works with OpenAI, Google, Anthropic, Azure OpenAI, and self-hosted models. Platform code uses the same interface regardless of which model handles the request.

**Request routing**

The proxy routes requests to models based on configured strategy. Current configuration uses "usage-based-routing-v2" which distributes load across available models.

**Cost tracking**

Usage tracking captures token consumption per request. Cost per token gets configured for each model, allowing the platform to calculate and display costs per conversation.

**PII protection**

Presidio integration (when enabled) scans requests for personally identifiable information before sending them to external providers. See [Data Anonymization](../2_anonymization/) for details.

**Reliability**

Retry policies handle temporary failures. The configuration specifies retry counts for timeout errors, rate limit errors, and internal server errors.

## Benefits

Organizations can switch providers without rewriting code. This avoids vendor lock-in and enables choosing models based on cost, performance, or data residency requirements.

Centralized cost tracking shows AI spending across the platform. You can see which conversations or agents consume the most tokens.

The proxy applies data handling policies uniformly. PII protection, rate limiting, and audit logging work the same way for all platform operations.
