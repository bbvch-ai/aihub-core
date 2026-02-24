# Swiss-Sovereign Dual-Mode Inference: Swiss LLM Cloud + Air-Gapped Local vLLM

## Context

AI-Hub previously relied on a heterogeneous mix of inference providers:

- **Azure OpenAI** for text generation (GPT-5, GPT-4o-mini), embeddings (text-embedding-3-small/large), transcription,
  TTS, and image generation
- **Cohere** for reranking (rerank-english-v3.0)
- **llama.cpp** for optional local GPU/CPU inference (Gemma-3 4B/12B, Qwen-3 embedding/reranking)
- **Swiss LLM Cloud** as an optional secondary provider

This architecture had several problems:

- **Data sovereignty**: Azure OpenAI and Cohere route data through US-based services, violating the platform's
  Swiss-sovereignty principle
- **Model fragmentation**: Different models ran locally vs. in the cloud (Qwen-3 locally, Azure text-embedding-3 in
  cloud), producing different embedding dimensions (1024 vs 3072) and incompatible vector stores — migrating between
  setups required full re-embedding
- **Reranker divergence**: Cohere rerank-english-v3.0 in the cloud vs. Qwen-3-reranking locally produced different
  ranking behavior, making RAG results unpredictable across deployments
- **llama.cpp limitations**: No function calling support, limited context windows, poor multi-model GPU memory
  management
- **Complexity**: Five provider configurations (Azure, Cohere, Swiss LLM Cloud, llama.cpp GPU, llama.cpp CPU) with
  stage-specific logic in templates

## Decision Drivers

- **Swiss data sovereignty**: All inference must remain within Swiss infrastructure — no US cloud providers
- **Deployment parity**: Identical model families for embedding, reranking, OCR, and transcription in both local GPU and
  cloud setups so that migrating between them requires no re-embedding and produces predictable results
- **Air-gapped GPU**: Local GPU deployments must operate without any internet access
- **Single-GPU target**: The local setup must fit entirely on one NVIDIA RTX 6000 Pro (96 GB VRAM)
- **Function calling**: Text generation models must support native tool/function calling for agent workflows
- **Simplification**: Reduce the number of provider integrations and conditional template logic

## Decision

We adopt a **clean dual-mode architecture** where embedding, reranking, OCR, and transcription use the same model family
regardless of deployment mode. Text generation models differ between modes since GPU and cloud serve different
size/performance tiers.

### Mode 1: Cloud-Only (Non-GPU Deployments)

**Swiss LLM Cloud** becomes the sole external provider. Multiple text generation models are available at different
capability/cost tiers (see `litellm-config.yml.j2` for the current model list). Service-specific endpoints handle
embedding, reranking, transcription, and OCR workloads separately. Per-token pricing is registered in LiteLLM
`model_info` for cost tracking through Langfuse.

No local inference containers are deployed in cloud mode. Azure OpenAI and Cohere are removed entirely.

### Mode 2: Air-Gapped Local GPU (RTX 6000 Pro 96 GB)

All inference runs locally via **vLLM** (replacing llama.cpp). The GPU setup has **no access to Swiss LLM Cloud** — it
is completely air-gapped. A single multimodal model handles all text generation, including vision tasks:

| Container           | Model                                | VRAM Allocation   | Purpose                  |
| ------------------- | ------------------------------------ | ----------------- | ------------------------ |
| `vllm`              | `Qwen/Qwen3-VL-30B-A3B-Instruct-FP8` | 85% (~82 GB)      | Text generation + vision |
| `vllm-bge-m3`       | `BAAI/bge-m3`                        | 3% (~3 GB)        | Embeddings (1024-dim)    |
| `vllm-bge-reranker` | `BAAI/bge-reranker-v2-m3`            | 3% (~3 GB)        | Reranking                |
| `speaches`          | `Systran/faster-whisper-large-v3`    | ~4% (~4 GB)       | Transcription            |
| `mineru-vlm`        | `MinerU2.5-2509-1.2B`                | ~5% (~5 GB)       | OCR/document parsing     |
| **Total**           |                                      | **~95% of 96 GB** |                          |

The single Qwen3-VL-30B model (Mixture-of-Experts, 3B active parameters from 30B total) replaces the previous
two-container approach (Gemma 4B + Mistral 24B). This simplifies the GPU setup to one text generation container while
providing multimodal capabilities (vision) and function calling support with a 131K context window.

### Shared Model Families Across Both Modes

The critical design choice: **embedding, reranking, OCR, and transcription use the same model family** in both modes:

- **BGE-M3** (1024-dim embeddings) in both local vLLM and Swiss LLM Cloud — no re-embedding needed when switching
  deployment modes
- **BGE-Reranker-v2-m3** in both modes — predictable ranking behavior regardless of where inference runs
- **MinerU VLM** in both modes — consistent document parsing quality
- **Whisper Large v3** in both modes (faster-whisper locally, standard whisper in cloud) — consistent transcription

Text generation models intentionally differ: the GPU runs a single multimodal model optimized for the 96 GB budget,
while the cloud offers multiple models at different capability/cost tiers. Local and cloud text generation models have
distinct names — there is no automatic fallback between them.

### Model Naming Convention

LiteLLM `model_name` uses the **real canonical model name** prefixed by role, making the actual model transparent to
operators:

| Before (generic)                     | After (canonical)                                                                        |
| ------------------------------------ | ---------------------------------------------------------------------------------------- |
| `text-generation/nano`               | `text-generation/Qwen3-VL-30B-A3B-Instruct-FP8` (GPU)                                    |
| `text-generation/mini`               | `text-generation/Mistral-Small-3.2-24B-Instruct-2506` (cloud)                            |
| `text-generation/large`              | Removed (multiple cloud models cover this tier)                                          |
| `embedding/small`, `embedding/large` | `embedding/bge-m3` (single model)                                                        |
| `reranker`                           | `reranker/bge`                                                                           |
| `transcription/whisperx`             | `transcription/faster-whisper-large-v3` (GPU) / `transcription/whisper-large-v3` (cloud) |
| `text-generation/ocr`                | `text-generation/MinerU2.5-2509-1.2B`                                                    |

The `litellm_params.model` field contains the cloud API alias (e.g., `openai/mistral3`) or local vLLM served name (e.g.,
`openai/qwen3-vl-30b`), while `model_name` is always the canonical identifier.

### Air-Gap Enforcement

The Jinja2 template uses `has_local_models` (derived from `gpu_enabled`) to conditionally include models:

- GPU configs: Only local models appear. No Swiss LLM Cloud endpoints or credentials are referenced.
- CPU configs: Only cloud models appear. No local inference containers are deployed.

This is enforced at the template level — generated configs never mix modes.

### Infrastructure Changes

- **vLLM replaces llama.cpp**: vLLM (v0.15.1) provides proper multi-model GPU memory management via
  `--gpu-memory-utilization`, native function calling, and 131K context windows
- **Single text generation container**: One vLLM instance with Qwen3-VL-30B replaces two (Gemma + Mistral), reducing
  operational complexity and maximizing VRAM for the primary model
- **CPU local inference removed**: Non-GPU compose files no longer start any local model containers — they are purely
  cloud-backed
- **Speaches GPU-only with separate volume**: Audio transcription runs exclusively on GPU. Uses a dedicated
  `speaches-models` volume (not shared with vLLM's `huggingface` cache) to avoid permission conflicts between containers
  running as different users
- **Capabilities dropped**: Image generation (DALL-E 3) and text-to-speech are removed as they had no Swiss-sovereign
  alternative

### Environment Configuration

Five service-specific Swiss LLM Cloud endpoint pairs replace the previous Azure/Cohere credentials:

- `SWISS_LLM_CLOUD_API_BASE_URL` / `_KEY` — text generation
- `SWISS_LLM_CLOUD_EMBEDDING_API_BASE_URL` / `_KEY` — embeddings
- `SWISS_LLM_CLOUD_RERANKING_API_BASE_URL` / `_KEY` — reranking (Jina AI-compatible)
- `SWISS_LLM_CLOUD_WHISPER_API_BASE_URL` / `_KEY` — audio transcription
- `SWISS_LLM_CLOUD_OCR_API_BASE_URL` / `_KEY` — document OCR

Local GPU models use `LOCAL_LLM_TOKEN` for vLLM API authentication. Cost is zero for all local models.

## Consequences

### Positive

- **Full Swiss sovereignty**: All inference — cloud and local — stays within Swiss infrastructure
- **Air-gapped GPU**: Local deployments operate without any internet dependency, suitable for classified environments
- **Seamless migration between modes**: Identical embedding and reranking models mean switching from GPU to cloud (or
  vice versa) requires no re-embedding and produces identical retrieval behavior
- **Consistent document parsing**: Same MinerU VLM in both modes ensures parsing quality is deployment-independent
- **Function calling everywhere**: vLLM Qwen3-VL-30B supports native tool calling, unblocking agent workflows that
  llama.cpp could not serve
- **Multimodal local inference**: Qwen3-VL handles both text and vision tasks in a single model
- **Simplified template logic**: Single `has_local_models` / `gpu_enabled` boolean replaces complex per-stage,
  per-service conditionals
- **Predictable GPU budget**: Explicit `--gpu-memory-utilization` per container prevents OOM and makes capacity planning
  transparent
- **Cost visibility**: Per-token pricing in LiteLLM enables cost tracking and comparison across cloud models via
  Langfuse
- **Cloud model flexibility**: New cloud models can be added or swapped in the LiteLLM config without code changes

### Negative

- **Single-vendor cloud dependency**: Swiss LLM Cloud is now the sole external provider — an outage affects all non-GPU
  deployments with no fallback
- **Capabilities removed**: No image generation or TTS until Swiss-sovereign alternatives are available
- **Re-embedding required**: Existing deployments using Azure text-embedding-3-large (3072-dim) must rebuild all Milvus
  collections for BGE-M3 (1024-dim)
- **Tight GPU fit**: ~95% of 96 GB leaves limited headroom for model upgrades on the same card
- **No cloud fallback for GPU**: Air-gapped design means GPU failures cannot be mitigated by routing to cloud

### Trade-offs

- **Sovereignty vs. provider diversity**: Dropping Azure/Cohere eliminates fallback options but enforces the platform's
  core privacy promise
- **Model parity vs. flexibility**: Using the same embedding/reranking models in both modes constrains cloud model
  choice but guarantees migration safety
- **Air-gap vs. resilience**: Fully offline GPU operation maximizes data sovereignty but prevents cloud-assisted
  recovery
- **Single model vs. multi-model GPU**: One large Qwen3-VL-30B with 85% VRAM is simpler and more capable than two
  smaller models, but leaves no room for a secondary text generation model
- **GPU utilization vs. headroom**: Maximizing the RTX 6000 Pro delivers strong local performance but limits future
  expansion without hardware changes
