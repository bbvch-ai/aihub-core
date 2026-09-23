# LiteLLM Config Variants Selected Per Deployment

## Context

One model entry in the LiteLLM config has to be served by different providers on different deployments: the default chat
model `text-generation/gemma-4-31B-it` moves to stoney-cloud on staging and production while every other deployment
stays on Infomaniak.

Only part of that is expressible in environment variables. LiteLLM resolves `os.environ/` recursively over the whole
config, so `api_base` and `api_key` can come from the environment — but the values arrive as **strings** and nothing
coerces them, because `litellm.types.router.ModelInfo` is `extra="allow"` and does not declare `max_input_tokens` or the
cost fields. A string there breaks the `context_window` arithmetic in `LLMConfig.to_llama_index` and is silently dropped
by `ModelInfoDTO._keep_only_parseable_fields`. The declared window and the per-token costs therefore have to stay
literal YAML numbers, and they differ per provider (100000 vs 155648, CHF 0.20/0.40 vs 0.25/1.00).

A build-time conditional cannot express it either. `generate_release` renders every bundle with `stage='latest'`
regardless of channel, and the nightly VM deploys from a bundle too, so a `stage` test would catch nightly as well. A
channel variable would be worse than useless: the `latest` bundle is deployed by **every** customer, and which provider
serves a model is a property of a customer's contracts, not of a release channel.

## Decision Drivers

- **Per-deployment, not per-build** The same released artifact must serve different providers on different VMs.
- **Correct `model_info` per provider** The declared window and costs must match whoever actually answers.
- **Fast rollback** Undoing a bad switch must not require a code revert and a republished bundle, especially since
  `ansible-pull` overwrites manual edits within 15 minutes.
- **Loud failure** A misconfigured selector must stop the proxy, not silently serve the wrong provider.
- **Room for a second provider at once** [aihub-requests#9](https://github.com/bbvch-ai/aihub-requests/issues/9) needs
  both providers live under one `model_name` with `order`-based failover.

## Decision

The LiteLLM config gains a **third rendering axis** beside stage and hardware: `LITELLM_VARIANTS` in
`generate_compose.py`. Any `CONFIG_SPECS` entry whose name pattern contains `{variant}` is rendered once per entry;
everything else keeps its two-axis shape. Both files ship in every compose file and every release bundle, mounted side
by side, and the deployment picks one at `docker compose up` through compose interpolation:

```yaml
command: --config /app/config.${LITELLM_CONFIG_VARIANT}.yml
```

The selector is named for the mechanism rather than the provider, so a variant holding two providers does not make the
name a lie. The compose template iterates the same `LITELLM_VARIANTS` list the renderer does, so adding a variant cannot
produce a config that nothing mounts.

## Consequences

- Switching or rolling back a provider is one vault value plus a `litellm` restart — and a restart of every API, agent
  and pipeline process, because `_fetch_all_model_info_cached` is a process-lifetime `lru_cache` with no invalidation.
- The generated litellm configs double, from 10 files to 20. The `.gpu` variants serve local vLLM models and carry no
  cloud chat block, so their two files are byte-identical; the duplication is accepted rather than special-cased.
- An unset or misspelled `LITELLM_CONFIG_VARIANT` points `--config` at a file that does not exist and LiteLLM refuses to
  start. That is deliberate: a silent fallback would serve the wrong provider at the wrong price.
- Every deployment needs both providers' credentials present, even the ones not using stoney, so the flip needs no new
  secrets.
- #9 extends this by adding a `stoney-primary` variant carrying both entries under one `model_name` with `order: 1` and
  `order: 2`. Selector, axis and vault key are unchanged.
- A larger declared window is not free elsewhere: a single turn between the old 100000 and the new 155648 can serialize
  past NATS's 1 MB `max_payload`, and the run then stalls with no error surfaced. The token guard cannot prevent it — it
  measures tokens, the limit is bytes.
