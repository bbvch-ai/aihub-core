# Legacy RAG Pipelines: Code Removed, Images Frozen, Names Reserved

## Context

Before the Generic Document Ingestion Pipeline, a knowledge database was served by a pipeline bound to one bucket at
deploy time. Two such deployments exist: `default_rag_pipeline` (`AIHubSettings().DEFAULT_BUCKET_NAME`,
`defaultknowledge`) and `shared_rag_pipeline` (`SHARED_BUCKET_NAME`, `sharedknowledge`). Both are built by
`default_definitions`, the public SDK builder for fixed-bucket pipelines.

`document_ingestion_pipeline` supersedes them entirely: one deployment serves every knowledge database, resolving its
target per run. Nothing new is ever assigned to a legacy pipeline — `IngestorType.selectable()` offers only
`document_ingestion` — so the two remaining deployments exist solely to keep ingesting into corpora that already exist.

Keeping them alive is not free. Route-per-run forked the whole Stage-2 storage surface into ~12 `routed_*` modules, each
a twin of a non-routed counterpart differing only in *how it learns the bucket*. After the legacy apps stop being
deployed, the non-routed set is maintained only for them and for a dev example — and the `routed_` prefix names a
distinction that no longer distinguishes anything.

## Decision Drivers

1. **A half-migration is worse than either end of it.** Two parallel store-construction paths for one job, and a prefix
   that disambiguates from files nobody uses, cost more in confusion than the legacy pipelines are worth.
2. **Existing corpora must keep working.** A customer running `defaultknowledge` today cannot be forced into a data
   migration by a platform upgrade.
3. **Frozen must mean frozen.** Anything that implies the legacy images still receive changes — a build context, a
   `latest` tag, a code location in a stage that does not run them — is a promise the platform cannot keep.

## Decision

**Delete the legacy pipelines' code; keep their last published images pinned, in the stages that run them, forever.**

- **The code is gone.** `app/default_rag_pipeline`, `app/shared_rag_pipeline`, `default_definitions` and the ~12
  non-routed Stage-2 twins are deleted, and the `routed_` prefix is dropped from the modules that outlive them. The
  prefix survives only on the six wrapper resources whose non-routed counterparts are still used by Stage 1.

- **Removing `default_definitions` is a breaking SDK change**, accepted deliberately rather than deprecated: it built
  fixed-bucket pipelines, which is the model being retired. `document_ingestion_pipeline_definitions` replaces it and is
  now the exported builder.

- **The images are pinned to their last release** (`v0.319.0`) in `nightly` and `latest` only. They carry no `build` or
  `local` key, so they render in no other stage; the compose template's build branch is removed, since the Dockerfile it
  referenced no longer exists. CI leaves them alone by construction: image discovery requires `build: localbuild`, and
  the `latest` retagging step requires a `:latest` tag.

- **The Dagster workspace is guarded on the same image tags as the compose services**, so a code location can no longer
  outlive its container. This is what actually went wrong before: the services were commented out of `compose-config`
  but left in `workspace.yml.j2`, giving every deployed stage two permanently-errored code locations.

- **There is no migration path.** A deployment that needs any change to a legacy corpus re-uploads it into a new
  self-service knowledge database. Re-pointing the existing buckets at `document_ingestion_pipeline` is not offered: the
  two pipelines would then both claim the same bucket, and the embedding model a corpus was ingested with is not
  recorded anywhere that a re-ingestion could honour.

- **The legacy names stay reserved.** `defaultknowledge` and `sharedknowledge` are rejected as knowledge database names,
  and `default_rag`/`shared_rag` remain in `IngestorType` and in `IngestorEntity.reserved_ids()` even though no code
  reads them any more. Without this, a new database could be created on the name of a frozen corpus and ingested on top
  of it by a pipeline that does not own it.

## Consequences

### Positive

- One store-construction surface and one naming scheme; the `routed_` prefix no longer implies a variant that exists.
- Compose and workspace cannot drift: both derive legacy presence from a single image tag.
- Frozen is expressed structurally — no build context, no floating tag — rather than by convention.
- The playground moves onto the real pipeline, so the dev example and the deployed article are the same code.

### Trade-offs

- **Legacy bugs can no longer be fixed.** A published image cannot receive a patch, and the branch that could build one
  no longer contains the code. Shipping a legacy fix would mean cutting a maintenance branch from the last release that
  contained it — a policy that must exist *before* it is needed, tracked as a follow-up.
- **Downstream users of `default_definitions` break on upgrade** with no deprecation window.
- **Two dead names are reserved forever**, in `IngestorType` and in the controller's reserved set, long after anything
  reads them.

### Related Decisions

- `2026_06_18_rag_pipeline_route_per_run.md` — the configurable pipeline that supersedes these (premise)
- `2026_07_18_self_service_knowledge_deletion.md` — legacy databases are undeletable, which is why their names must be
  reserved rather than freed
