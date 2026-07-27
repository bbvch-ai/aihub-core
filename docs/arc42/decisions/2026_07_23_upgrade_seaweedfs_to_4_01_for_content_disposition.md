# Upgrade SeaweedFS 3.97 → 4.01 to Honor Presigned Content-Disposition

## Context

Clicking **Download** on a knowledge base file opened previewable types (pdf, image, txt, md) **inline in a new browser
tab** instead of prompting a save dialog, while non-previewable types (e.g. `.docx`) already downloaded — an
inconsistent, confusing experience (issue #51). The download button calls `window.open(presignedUrl)`, and our S3
objects carry **no `Content-Disposition`** header, so the browser renders previewable content inline.

The clean, memory-safe fix is to force `Content-Disposition: attachment` on the presigned GET URL via the S3
`response-content-disposition` query override — a native streaming download with no in-browser buffering. But
**SeaweedFS 3.97 silently ignores that override**: it returns the object with default headers regardless. This is an
upstream bug, fixed in [PR #7559](https://github.com/seaweedfs/seaweedfs/pull/7559) ("s3api: Fix
response-content-disposition query parameter not being honored"), first released in **SeaweedFS 4.01** (2025-11-28).

The alternative — a client-side blob download (`fetch` → Blob → `<a download>`) — works on 3.97 but buffers the **entire
file in browser memory** with no streaming or progress, which is unacceptable for large documents.

`ghcr.io/bbvch-ai/aihub-core/seaweedfs` is a **mirror** of the upstream `chrislusf/seaweedfs` image (via
`make mirror-image`), pinned in `infra/deployment/compose-config.yml`. Moving from 3.97 to 4.01 crosses a **major
version boundary** (4.00 + 4.01) that carries real architectural and operational changes, so this is a deliberate
decision, not a routine tag bump.

## Decision Drivers

- **Correctness + memory safety** — the download must stream to disk natively, not buffer in the browser. Only the
  `Content-Disposition` approach satisfies both, and only ≥4.01 honors it.
- **No blast-radius regressions** — every service reads/writes the same `seaweedfs-s3` gateway (Milvus, Langfuse,
  ClickHouse backups, OpenWebUI, LiteLLM, the ingestion pipeline, agent uploads, and the backup/restore service). The
  upgrade must not break any of them.
- **Data continuity** — existing on-disk volume data and the etcd-backed filer metadata must survive the major bump.
- **Minimal, reversible code surface** — the application change should be small and default to today's behavior for all
  existing callers.

## Decision

Upgrade SeaweedFS **3.97 → 4.01** and use the now-honored override to force downloads only where intended.

1. **Version bump.** `infra/deployment/compose-config.yml` `image_tags.seaweedfs: seaweedfs:3.97 → 4.01`; mirror 4.01
   into GHCR (`make mirror-image`) before non-dev stages pull it; `make generate-compose` regenerates all 10 compose
   files (master/volume/filer/s3).

2. **Opt-in disposition, defaulting to current behavior.** `S3AnonymousFileAccessService.generate_sas_url` gains an
   optional `response_content_disposition: str | None = None`; when set, it is passed as `ResponseContentDisposition`
   into the presigned `get_object`. Default `None` preserves inline behavior, so the other callers of this shared method
   (RAG figure signing per ADR `2026_07_10_inline_rag_figures_as_base64`, and the generic file controller) are
   untouched — no new abstraction.

3. **Download vs preview split at the endpoint.** The knowledge document-URL endpoint gains a `download: bool = False`
   query param, threaded to `KnowledgeService.get_document_url(..., as_attachment=)`, which builds
   `attachment; filename="<key-basename>"`. The frontend **Download** button requests `download=true` and triggers the
   URL via a programmatic anchor click (no orphan blank tab); **"Open original document"** keeps inline preview
   (`download=false`, the default).

### Breaking-change awareness (3.97 → 4.01)

The 4.x line is a genuine architectural shift, not just the disposition fix:

- **Direct S3 → volume-server data path** (4.01 #7481, #7518) — S3 no longer routes object data through the filer;
  volume reads/writes require **JWT** (3.99 #7376, 4.01 #7514). All four SeaweedFS services share
  `WEED_JWT_SIGNING_KEY`, so internal auth continues to work.
- **Non-root container user** (4.00 #7399) + **`/data` ownership/permission fix** (4.01 #7451) — the primary upgrade
  risk on existing deployments. In our dev volumes the data files are already owned by the host user, so no
  permission break occurred; **production upgrades must verify (and if needed `chown`) the mounted volume ownership.**
- **Bucket-policy enforcement** (4.01 #7471), **auto-create bucket** (4.01 #7549), path/virtual-style addressing
  changes (3.99 #7357), and S3 error-code changes (3.98: 400 vs 500) — none affected our path-style, explicit-identity
  configuration.

## Consequences

### Positive

- **The download bug is fixed the right way** — native, streaming, per-request `Content-Disposition: attachment`;
  verified live on 4.01 (preview URL returns no disposition; attachment URL returns `attachment; filename="..."`).
- **Minimal, reversible code change** — one optional kwarg + one query param; every pre-existing caller keeps its exact
  behavior.
- **Whole S3 blast radius re-verified on 4.01** — knowledge ingestion, agent uploads, RAG retrieval, Langfuse traces,
  OpenWebUI uploads, and a full `backup_asset_job` (postgres/ferretdb/neo4j/clickhouse/valkey/nats/milvus artifacts
  written + `head_object` confirmed) all pass. Existing volume data and buckets survived the bump intact.

### Trade-offs

- **We track a major upstream version** whose direct-volume-access + JWT model is newer and less battle-tested for us
  than 3.97; upstream 4.x regressions could surface in future point releases.
- **Production rollout needs the two operational steps** the dev upgrade could skip: mirror 4.01 to GHCR first, and
  verify/adjust volume-mount ownership for the non-root container user before starting.
- **Filename header is not RFC 6266-encoded** — the attachment filename is the S3 key basename interpolated directly;
  unusual characters (embedded quotes, non-ASCII, control chars) are not escaped. Acceptable because keys derive from
  constrained upload filenames, but a future hardening could add `filename*=UTF-8''<encoded>`.
