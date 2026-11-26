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

### Names, purpose and capabilities

Model pickers in the Admin UI read three more keys from `model_info`:

- **`aihub_display_name`:** the name a picker shows, such as `Gemma 4 31B`. Every model in the shipped configuration
  sets it. A model without it is shown by its `model_name` without the prefix (`gemma-4-31B-it`).
- **`aihub_general_purpose`:** `false` for a model built for one job, which pickers then never offer. Only the OCR model
  `MinerU2.5-2509-1.2B` sets it to `false`: it is served over the chat API, so its `mode` stays `chat`, but it cannot
  hold a conversation. `GET /models/mode/{mode}` leaves such models out unless the call sets
  `include_special_purpose=true`, and an agent or process profile or a knowledge database that names one is refused when
  saved. A model without the key counts as general-purpose.
- **`supports_reasoning`:** whether the model can produce a thinking phase at all, next to the existing
  `supports_function_calling`, `supports_response_schema` and `supports_vision`. A picker that requires a capability
  treats a flag that is not set as unsupported.

```yaml
  - model_name: text-generation/MinerU2.5-2509-1.2B
    model_info:
      aihub_display_name: MinerU 2.5 (OCR)
      aihub_hosting_location: swiss_cloud
      aihub_general_purpose: false
      mode: chat
      supports_function_calling: false
      supports_response_schema: false
      supports_vision: true
      supports_reasoning: false
```

The configuration generator refuses a `mode: chat` model that does not set all four `supports_*` flags and
`aihub_general_purpose` to `true` or `false`. A model added through the LiteLLM UI skips that check: it stays
selectable, but is left out of every picker that requires a capability it does not declare.

LiteLLM passes a request's `reasoning_effort` on to every model it does not know, whatever `supports_reasoning` says. If
a provider rejects it, list it in the model's `additional_drop_params`, as the configuration does for Ministral.

### Embedding and reranking models

The platform sizes every input to an embedding or reranking model before sending it: document chunks at ingestion,
search queries, and each query/document pair of a rerank. A model rejects an input over its window with an error instead
of truncating it, so the count must be the model's own. Each `mode: embedding` or `mode: rerank` entry therefore
declares two keys next to `max_input_tokens`:

- **`aihub_tokenizer`:** the id of a tokenizer vendored in `packages/core` under
  `swiss_ai_hub/core/generative_ai/resources/tokenizers/vendored/`. The platform counts with it in-process, without a
  network call. `bge-m3` covers BAAI/bge-m3 and BAAI/bge-reranker-v2-m3, which share one tokenizer.
- **`aihub_input_overhead_tokens`:** the special tokens the model adds to every input. bge-m3 adds 2 (`<s> text </s>`),
  the bge reranker 4 per pair (`<s> query </s></s> document </s>`).

```yaml
  - model_name: embedding/bge-m3
    model_info:
      mode: embedding
      max_input_tokens: 8192
      aihub_tokenizer: bge-m3
      aihub_input_overhead_tokens: 2
```

A model without `aihub_tokenizer` still works: its inputs are counted with tiktoken and kept well inside its window, as
before these keys existed, and each process logs one warning naming the model. To count a new model exactly, add a
folder under `vendored/` with the tokenizer file, its `LICENSE` and a `SOURCE.json` (repository, revision, file, sha256,
format), then name the folder's id in the config. A unit test checks that every embedding and reranking model in the
generated configs names a vendored tokenizer.

Apps read these keys once per process. After changing them, recreate the LiteLLM container first, then restart the apps.

## Core functions

Unified interface: LiteLLM provides an OpenAI-compatible API that works with Swiss LLM Cloud, locally hosted vLLM
models, and other providers. Platform code uses the same interface regardless of which model handles the request.

Request routing: The proxy routes requests based on configured strategy. Current configuration uses "simple-shuffle":
every model group has a single deployment, so a usage-based strategy would only add a Redis write to every call.

Response caching: Only embeddings are cached in Valkey, for 24 hours. Chat completions are not cached, because their
prompts carry whole attached files and are almost never repeated.

Cost tracking: Usage tracking captures token consumption per request. Cost per token is configured for each model,
allowing the platform to calculate and display costs per conversation. See [Cost control](../../14_cost_control/) for
details on cost tracking and optimization.

PII protection: the `pii-anonymisation` guardrail replaces personal data in every chat request to a model hosted outside
the deployment with placeholders and restores them in the answer, streamed or not. See
[Data Anonymization](../2_anonymization/) for details.

Retry policies: The configuration specifies retry counts for timeout errors, rate limit errors, and internal server
errors.
