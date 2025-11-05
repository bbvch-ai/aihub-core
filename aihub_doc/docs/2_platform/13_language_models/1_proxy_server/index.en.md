---
title: Proxy server
index: 1
---

# LLM proxy

The LLM proxy (LiteLLM) provides a centralized gateway to language model providers. It abstracts vendor-specific APIs
behind an OpenAI-compatible interface, allowing the platform to work with multiple AI providers without changing code.

## Configuration

Models are configured in the LiteLLM configuration file. Each model entry specifies the provider, API endpoint,
authentication, and capabilities.

::: details Example model configuration:
```yaml
model_list:
  - model_name: azure/gpt-4o-mini
    litellm_params:
      model: azure/gpt-4o-mini
      api_base: https://your-resource.openai.azure.com/
      api_key: os.environ/AZURE_OPENAI_KEY
      api_version: "2024-12-01-preview"
    model_info:
      mode: chat

  - model_name: google/gemini-2.5-flash
    litellm_params:
      model: gemini/gemini-2.5-flash
      api_key: os.environ/GEMINI_API_KEY
    model_info:
      mode: chat

  - model_name: local/qwen-2.5-multimodal-small
    litellm_params:
      model: openai/Qwen2.5-VL-3B-Instruct
      api_base: http://llama-cpp:8182/v1
      api_key: None
    model_info:
      mode: chat
      supports_function_calling: true
      supports_vision: true
```

The `model_name` identifies the model in agent configurations. The `litellm_params` section contains provider-specific
connection details. The `model_info` section specifies capabilities like chat, embedding, vision, or function calling.
:::

## Core functions

Unified interface: LiteLLM provides an OpenAI-compatible API that works with OpenAI, Google, Anthropic, Azure OpenAI,
and self-hosted models. Platform code uses the same interface regardless of which model handles the request.

Request routing: The proxy routes requests based on configured strategy. Current configuration uses
"usage-based-routing-v2" which distributes load across available models.

Cost tracking: Usage tracking captures token consumption per request. Cost per token is configured for each model,
allowing the platform to calculate and display costs per conversation. See [Cost control](../../14_cost_control/) for
details on cost tracking and optimization.

PII protection: Presidio integration (when enabled) scans requests for personally identifiable information before
sending them to external providers. See [Data Anonymization](../2_anonymization/) for details.

Retry policies: The configuration specifies retry counts for timeout errors, rate limit errors, and internal server
errors.
