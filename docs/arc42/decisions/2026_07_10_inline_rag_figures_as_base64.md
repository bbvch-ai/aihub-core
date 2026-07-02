# Inline RAG Figures as Base64 at the LiteLLM Gateway

## Context

When a RAG assistant retrieves a document chunk that is a **figure** (image), the agent attaches the image to the LLM
prompt so a vision model can use it. At query time `combine_nodes_in_order` (in `packages/core/.../retrieval/`) turns
each figure into a LlamaIndex `ImageBlock` that is sent to the model through LiteLLM.

Delivering a figure as a **URL** requires whoever consumes the message to fetch that URL. The LLM provider dereferences
image URLs **server-side**: on CPU (non-GPU) deployments every text-generation model is served by **Infomaniak managed
inference** (`SWISS_LLM_CLOUD_API_BASE_URL`) — see ADR `2026_06_29_resilience_for_reasoning_models_on_infomaniak`.
LiteLLM forwards the `image_url` to Infomaniak unchanged (verified via `--detailed_debug` raw request logging), and
Infomaniak's image fetcher pulls it through **its own egress proxy**, which cannot reach our self-hosted object storage
(a figure URL → `403`). By contrast, sending the image **inline as a base64 `data:` URL** returns `200` with a correct
description, because no party has to fetch anything — the image bytes travel inside the request.

An earlier fix (PR #1547) embedded the base64 directly in the agent's `ImageBlock`. Review flagged that this **bloats
NATS/JetStream events**: the base64-laden `ChatMessage` rides on control events (`InOrderNodeCombinerEvent`,
`LimitChatHistoryWithContextEvent`, `LLMEvent`), which are published to NATS (max_payload 1 MB dev / 2 MB prod),
persisted to Mongo, and shipped to Langfuse — a few figures per turn would exceed the limit and be rejected.

## Decision Drivers

- **The provider, not the cluster, dereferences the image** — image delivery cannot depend on the agent being the
  fetcher, and the provider cannot reach our storage.
- **Keep base64 off the event bus** — the heavy bytes must not touch NATS/JetStream/Mongo/Langfuse, which are payload-
  capped and observability-facing.
- **Deployment-topology independence** — the same agent code runs against external managed inference (Infomaniak) and,
  on GPU deployments, local vLLM. It must be possible to turn inlining off where the provider can resolve the URL
  itself.
- **Bounded request cost** — inlining moves image bytes into the request; this must be capped so a large figure cannot
  blow the context window or run up vision-token cost unboundedly.

## Decision

Keep the small presigned **URL** in the agent message/events, and convert URL→base64 **inside the LiteLLM proxy** via a
pre-call hook, just before the provider call. The LiteLLM container is in-cluster and can reach `seaweedfs-s3`, so it
fetches the object and inlines it; the heavy base64 exists only transiently at the gateway and never touches
NATS/Mongo/Langfuse.

1. **Agent emits a presigned URL (internal or public).** Presigned URLs are host-bound, so
   `S3AnonymousFileAccessService.generate_sas_url` gains an `internal: bool = False` flag. When inlining is enabled
   `combine_nodes_in_order` signs the figure against the **internal** endpoint (`http://seaweedfs-s3:9000`) so the
   in-cluster LiteLLM can fetch it; when disabled it signs the **public** URL (pre-inlining behaviour) for the provider
   to fetch directly. The four browser-facing callers keep the public-signed default. The message stays tiny — just the
   URL.

2. **LiteLLM pre-call hook inlines base64.** A bind-mounted `CustomLogger`
   (`infra/deployment/templates/litellm_functions/custom_callbacks.py`, stdlib + `httpx` only — it cannot import
   `swiss_ai_hub.*`) walks `data["messages"]`; for each `image_url` part whose host matches the internal S3 host
   (`S3_STORAGE_ENDPOINT`), it downloads the object and replaces the URL with `data:<content-type>;base64,<…>`. The hook
   is bind-mounted with the same precedent as OpenWebUI functions (`STATIC_COPY_DIRS`), since the `litellm` service is a
   mirrored upstream image with no Dockerfile.

3. **Env-driven behaviour.** `RAG_IMAGE_INLINE_ENABLED` (default `true`, read by both the agent and the gateway) turns
   the whole path off: the agent signs the public URL and the gateway passes it through, reverting to the pre-inlining
   behaviour. `RAG_IMAGE_INLINE_MAX_BYTES` (default 5 MB, gateway-only) caps the inline size. A figure that fails to
   download or exceeds the cap **degrades to a short text marker** in place of the image
   (`[failed to fetch figure/image]` / `[figure omitted: exceeds size limit]`), so one bad figure never fails the whole
   LLM call.

This changes only the agent's figure→LLM path and the gateway. Browser-facing image links (knowledge/file views) are
unaffected — they keep the public-signed URL.

### Endpoints: connect vs sign

Three S3 endpoints are kept distinct because presigned URLs are **signed offline** (no connection) but must carry the
host their eventual *fetcher* can reach:

- `S3_STORAGE_ENDPOINT` — where a process **connects** for real S3 operations (uploads, head_bucket, downloads). Must be
  reachable: `localhost:9000` for host-run dev services, `seaweedfs-s3:9000` in-cluster.
- `S3_STORAGE_PUBLIC_ENDPOINT` — host baked into **browser-facing** presigned URLs (`s3.${DOMAIN}` / `localhost:9000`).
- `S3_STORAGE_INTERNAL_ENDPOINT` — host baked into **figure** presigned URLs, fetched by the in-cluster LiteLLM gateway
  (`seaweedfs-s3:9000`). Falls back to `S3_STORAGE_ENDPOINT` if unset (so in-cluster deployments need not set it).

Signing is offline, but the agent also **downloads** the figure client-side when it token-counts the context during
chat-history limiting (`TokenCounter.estimate_tokens_in_messages` → `ImageBlock.resolve_image` → `requests.get`). So a
**host-run** agent (`make run-rag-agent`) does connect to `seaweedfs-s3:9000` and needs it to resolve. Local dev
therefore requires a one-time host alias for the **figure** path:

```
127.0.0.1 seaweedfs-s3   # add to /etc/hosts
```

The separate endpoints still matter: with `S3_STORAGE_ENDPOINT=localhost:9000`, the API and text-only RAG start and run
**without** the alias — only figure retrieval needs it. Alternatively, run the agent in-cluster (`make up-build`), which
resolves `seaweedfs-s3` natively and needs no alias — the closest match to production, where the agent and gateway are
both in-cluster.

## Consequences

### Positive

- **Figures work regardless of who serves the model**, and the base64 never rides on the event bus — NATS/Mongo/Langfuse
  payloads stay small (only the URL). Prototype: the exact URL that used to 403 now returns 200 with a correct image
  description.
- **Topology-independent and toggleable** — the same path works for managed inference and local vLLM, and inlining can
  be turned off per deployment without code changes.
- **Bounded request cost** — the size cap protects the context window and vision-token budget.

### Trade-offs

- **We own a LiteLLM callback** that must be maintained across upstream LiteLLM upgrades.
- **The hook re-downloads the figure per call** (no cache); the bytes travel on every turn that retrieves a figure, plus
  base64's ~33% overhead.
- **The infra Python is not in the standard `make test` scope** — `test_custom_callbacks.py` is runnable via
  `uv run pytest infra/deployment/templates/litellm_functions/` but will not run in CI unless that path is wired.
- **Graceful degradation, easy to miss** — an unavailable or oversized figure is replaced by a small text marker and a
  logged warning rather than failing the call, so a persistently broken figure can go unnoticed unless logs are checked.
