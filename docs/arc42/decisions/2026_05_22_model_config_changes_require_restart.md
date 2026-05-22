# Model configuration changes require a service restart

## Context

Models available to the platform are defined in the LiteLLM configuration file
(`infra/configs/litellm/litellm-config.*.yml`, auto-generated from a Jinja2 template). LiteLLM reads this `model_list`
only at proxy startup — it does not watch the file or hot-reload it.

Independently, platform services that build LLM clients through `LiteLLMBase`
(`packages/core/swiss_ai_hub/core/generative_ai/resources/models/llm/lite_llm_base.py`) fetch the LiteLLM
`/v1/model/info` response once and cache it for the lifetime of the process. This affects the `api` and `agent` services
and every `LiteLLMBase` consumer (`LLMConfig`, `EmbeddingModelConfig`, `RerankingModelConfig`).

The result: model metadata is a startup-time snapshot at two layers — the LiteLLM proxy and every consuming service.

## Decision Drivers

- LiteLLM applies model configuration only on restart; a partial reload where consumers refresh but the proxy does not
  (or vice versa) would be inconsistent and confusing.
- Avoid cache-invalidation / TTL machinery for a value that changes rarely.
- The model list is deployment-time configuration — it lives in a committed, generated file, so changing it is already a
  deploy action, not a runtime operation.

## Decision

Model configuration changes are applied by restarting LiteLLM **and** every dependent service. Per-process caching of
model metadata is intentional and accepted.

Restart order:

1. Restart `litellm`; wait until it is healthy.
2. Restart `api`, `agent`, and any other service that uses models.

## Consequences

- Operators must restart the full set of services, not only LiteLLM. Restarting only LiteLLM leaves `api` / `agent`
  serving a stale model list, which surfaces as `ValueError: Model <name> not found in LiteLLM Proxy`.
- The restart order matters: a consumer restarted before LiteLLM is healthy re-caches a stale or empty model list.
  Always restart LiteLLM first.
- There is no runtime model hot-swap. If frequent live model changes become a requirement, this decision must be
  revisited — e.g. a TTL-based refresh of the `/v1/model/info` cache in `LiteLLMBase`.
