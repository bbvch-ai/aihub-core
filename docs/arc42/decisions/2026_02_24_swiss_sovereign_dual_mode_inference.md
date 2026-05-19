# Swiss LLM Cloud + Local vLLM: Clean GPU/Cloud Separation

## Context

Swiss AI Hub's inference setup had grown inconsistent across deployment modes:

- **CPU-based local models in `infra/docker-compose.dev.yml`**: The non-GPU dev compose ran llama.cpp on the CPU
  (Gemma-3 4B for chat, Qwen-3 0.6B for embedding/reranking). These models were slow and unreliable, causing flaky tests
  and poor developer experience. This violated the platform's deployment principle: non-GPU setups should use cloud
  inference, not struggle with CPU-bound local models.
- **Azure dependency with hidden test gaps**: Cloud inference routed through Azure OpenAI (GPT-5, GPT-4o-mini,
  text-embedding-3-small/large, DALL-E 3, transcription, TTS) and Cohere (reranking). Many tests were marked with
  `@pytest.mark.azure` and excluded from CI, silently hiding failures behind a marker instead of running against real
  models.
- **Swiss sovereignty violation**: Azure OpenAI is a US-based service. For a Swiss-first platform, routing inference
  data through US infrastructure contradicts the core data sovereignty promise.
- **Unspecific GPU targets**: GPU variants of docker-compose files did not specify what hardware they targeted. It was
  unclear whether they'd fit on a given GPU, and the memory budgets were not explicit.
- **Model fragmentation**: Different models ran in different modes — Qwen-3 locally, Azure text-embedding-3 in the cloud
  — producing different embedding dimensions (1024 vs 3072) and incompatible vector stores. Migrating between setups
  required full re-embedding.

## Decision Drivers

- **Enforce the deployment principle**: Non-GPU setups use cloud inference only, GPU setups use local inference only. No
  more CPU-bound local models as a compromise.
- **Swiss data sovereignty**: All cloud inference must stay within Swiss infrastructure.
- **CI reliability**: The CI pipeline (which uses `infra/docker-compose.dev.yml`) must run against real, fast models —
  not flaky CPU-bound local inference.
- **Explicit GPU target**: GPU compose files must target a specific card with explicit VRAM budgets per model so
  operators know exactly what hardware they need.
- **Model parity for embedding/reranking**: The same model families for embedding, reranking, OCR, and transcription in
  both modes so migrating between them requires no re-embedding.

## Decision

### Clean Mode Separation

We enforce a strict split: only GPU variants of docker-compose files run local inference containers. Non-GPU variants
have zero local model containers and route all inference through the cloud.

The Jinja2 template uses a single `has_local_models` boolean (derived from `gpu_enabled`) to conditionally include
models. Generated configs never mix modes.

### Non-GPU Mode: Swiss LLM Cloud

**Swiss LLM Cloud** replaces Azure OpenAI and Cohere as the sole cloud provider. This keeps all inference within Swiss
infrastructure.

Multiple text generation models are registered in LiteLLM with per-token pricing for cost tracking through Langfuse:

- `text-generation/Qwen3-VL-235B-A22B-Instruct` — large multimodal model, default for most interactions
- `text-generation/Mistral-Small-3.2-24B-Instruct-2506` — lightweight/cheap option
- `text-generation/Kimi-K2.5` — large context window (131K in / 65K out)
- `text-generation/Apertus-70B-Instruct-2509` — Swiss-AI foundation model

> **Update 2026-05-19:** `text-generation/gpt-oss-120b` was retired (no longer available on Swiss LLM Cloud). The
> default for most interactions, the LiteLLM fallback, and the prompt-injection detection model are now
> `text-generation/Qwen3-VL-235B-A22B-Instruct`.

Swiss LLM Cloud does not yet have a unified proxy, so each service type requires a separate endpoint:

- `SWISS_LLM_CLOUD_API_BASE_URL` / `_KEY` — text generation
- `SWISS_LLM_CLOUD_EMBEDDING_API_BASE_URL` / `_KEY` — embeddings (BGE-M3)
- `SWISS_LLM_CLOUD_RERANKING_API_BASE_URL` / `_KEY` — reranking (BGE-Reranker, Jina AI-compatible)
- `SWISS_LLM_CLOUD_WHISPER_API_BASE_URL` / `_KEY` — transcription (Whisper Large v3)
- `SWISS_LLM_CLOUD_OCR_API_BASE_URL` / `_KEY` — document OCR (MinerU)

Once Swiss LLM Cloud introduces a unified proxy, these should consolidate to a single endpoint pair.

### GPU Mode: Local vLLM on RTX 6000 Pro (96 GB)

The **NVIDIA RTX 6000 Pro** is selected as the target GPU: cheap, readily available, and 96 GB VRAM gives enough room
for all models. All local inference runs via **vLLM** (replacing llama.cpp) for fast, batched inference with explicit
GPU memory management via `--gpu-memory-utilization`.

| Container           | Model                                | VRAM Budget  | Purpose                  |
| ------------------- | ------------------------------------ | ------------ | ------------------------ |
| `vllm`              | `Qwen/Qwen3-VL-30B-A3B-Instruct-FP8` | 85% (~82 GB) | Text generation + vision |
| `vllm-bge-m3`       | `BAAI/bge-m3`                        | 3% (~3 GB)   | Embeddings (1024-dim)    |
| `vllm-bge-reranker` | `BAAI/bge-reranker-v2-m3`            | 3% (~3 GB)   | Reranking                |
| `speaches`          | `Systran/faster-whisper-large-v3`    | ~4% (~4 GB)  | Transcription            |
| `mineru-vlm`        | `MinerU2.5-2509-1.2B`                | ~5% (~5 GB)  | OCR/document parsing     |
| **Total**           |                                      | **~95%**     |                          |

The GPU setup is completely air-gapped — no Swiss LLM Cloud endpoints or credentials are referenced in GPU configs.

### Shared Model Families

Embedding, reranking, OCR, and transcription use the **same model family** in both modes:

- **BGE-M3** (1024-dim) for embeddings — no re-embedding when switching deployment modes
- **BGE-Reranker-v2-m3** for reranking — consistent ranking behavior
- **MinerU VLM** for document parsing — consistent OCR quality
- **Whisper Large v3** for transcription (faster-whisper locally, standard whisper in cloud)

Text generation models intentionally differ between modes: the GPU runs one multimodal model sized for the 96 GB budget,
while the cloud offers multiple models at different capability/cost tiers.

### CI Pipeline Impact

The `infra/docker-compose.dev.yml` (used in CI) no longer starts any local inference containers. CI tests run against
Swiss LLM Cloud models, which are fast and reliable. The `@pytest.mark.azure` test marker is removed from all scopes —
those tests now run normally against the cloud models instead of being silently excluded.

This required adding Swiss LLM Cloud secrets to GitHub Actions CI configuration.

### Model Naming: Abstract Tiers to Real Names

Previously, LiteLLM used abstract tier names like `text-generation/nano`, `text-generation/large`, `embedding/small`.
This made sense when agents were not configurable — the code just referenced a tier and the platform resolved it. With
the introduction of agent configuration (where admins choose models per agent profile in the Admin UI), abstract tiers
became a hindrance: admins need to see which actual model they're selecting, and the platform may offer many models that
don't fit into a simple small/medium/large hierarchy.

LiteLLM `model_name` now uses the real canonical model name prefixed by role — e.g.,
`text-generation/Mistral-Small-3.2-24B-Instruct-2506`, `embedding/bge-m3`, `reranker/bge`. The abstract tiers (`nano`,
`mini`, `large`, `small`) are removed entirely. See `litellm-config.yml.j2` for the current model list.

### Capabilities Dropped

Image generation (DALL-E 3) and text-to-speech (Kokoro) are removed — no Swiss-sovereign alternative is available.

## Consequences

### Positive

- **Swiss sovereignty enforced**: All inference stays within Swiss infrastructure
- **CI is fast and reliable**: Tests run against real cloud models instead of flaky CPU-bound llama.cpp
- **No more hidden test failures**: Azure test markers removed — all tests run in CI
- **Explicit GPU budget**: Operators know exactly what card to buy and how VRAM is allocated
- **No re-embedding on migration**: Same embedding/reranking models in both modes
- **Simplified template logic**: Single `has_local_models` boolean replaces complex per-stage, per-service conditionals
- **Cost visibility**: Per-token pricing in LiteLLM enables cost tracking across cloud models via Langfuse

### Negative

- **Model list maintenance**: The LiteLLM config must be kept in sync with the models available in Swiss LLM Cloud,
  including pricing updates
- **CI requires cloud secrets**: GitHub Actions must be configured with Swiss LLM Cloud credentials (10 secrets: 5
  endpoint pairs)
- **5 endpoint pairs for cloud**: Until Swiss LLM Cloud adds a unified proxy, each service type needs its own base URL +
  API key
- **Single-vendor cloud dependency**: Swiss LLM Cloud is the sole external provider — an outage affects all non-GPU
  deployments
- **Re-embedding required for existing deployments**: Deployments using Azure text-embedding-3-large (3072-dim) must
  rebuild Milvus collections for BGE-M3 (1024-dim)
- **Tight GPU fit**: ~95% of 96 GB VRAM leaves limited headroom for model upgrades on the same card
- **Capabilities removed**: No image generation or TTS until Swiss-sovereign alternatives appear
