---
title: Proxy server
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
  # Cloud model (Swiss LLM Cloud)
  - model_name: text-generation/gemma-4-31B-it
    litellm_params:
      model: openai/google/gemma-4-31B-it
      api_base: os.environ/SWISS_LLM_CLOUD_API_BASE_URL
      api_key: os.environ/SWISS_LLM_CLOUD_API_KEY
      drop_params: true
    model_info:
      mode: chat
      supports_function_calling: true
      input_cost_per_token: 0.0000002
      output_cost_per_token: 0.0000008

  # Local GPU model (vLLM)
  - model_name: text-generation/Qwen3-VL-30B-A3B-Instruct-FP8
    litellm_params:
      model: openai/qwen3-vl-30b
      api_base: http://vllm:8000/v1
      api_key: os.environ/LOCAL_LLM_TOKEN
      drop_params: true
    model_info:
      mode: chat
      supports_function_calling: true
      supports_vision: true
      input_cost_per_token: 0
      output_cost_per_token: 0
```

The `model_name` identifies the model in agent configurations using the real canonical model name. The `litellm_params`
section contains provider-specific connection details. The `model_info` section specifies capabilities and per-token
pricing for cost tracking through Langfuse.
:::

::: warning Applying configuration changes
LiteLLM reads `model_list` only at startup and does not watch the configuration file. Platform services (`api`, `agent`)
additionally cache model metadata for their process lifetime. To apply a model configuration change, restart LiteLLM
**and** every dependent service, in this order:

1. Restart `litellm` and wait until it is healthy.
2. Restart `api`, `agent`, and any other service that uses models.

Restarting only LiteLLM leaves the other services with a stale model list, which surfaces as
`Model <name> not found in LiteLLM Proxy` errors.
:::

## Core functions

Unified interface: LiteLLM provides an OpenAI-compatible API that works with Swiss LLM Cloud, locally hosted vLLM
models, and other providers. Platform code uses the same interface regardless of which model handles the request.

Request routing: The proxy routes requests based on configured strategy. Current configuration uses
"usage-based-routing-v2" which distributes load across available models.

Cost tracking: Usage tracking captures token consumption per request. Cost per token is configured for each model,
allowing the platform to calculate and display costs per conversation. See [Cost control](../../14_cost_control/) for
details on cost tracking and optimization.

PII protection: Presidio integration (when enabled) scans requests for personally identifiable information before
sending them to external providers. See [Data Anonymization](../2_anonymization/) for details.

Retry policies: The configuration specifies retry counts for timeout errors, rate limit errors, and internal server
errors.
