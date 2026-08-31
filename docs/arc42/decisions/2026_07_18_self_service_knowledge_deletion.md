# Self-Service Knowledge Deletion: Async Dagster Teardown + Soft-Delete State

## Context

Self-service knowledge databases can be created from the Admin UI (a `BucketEntity`, its S3 bucket, and namespaces), but
there was no way to remove one. Admins could add databases and namespaces they could never delete — an incomplete
lifecycle. This decision adds deletion of a whole knowledge database and of a single namespace, on the same branch as
the Generic Document Ingestion Pipeline (no separate issue).

A knowledge database and its namespaces are not one store — they span six:

| Layer                                             | Keyed by                                    | Database delete             | Namespace delete                       |
| ------------------------------------------------- | ------------------------------------------- | --------------------------- | -------------------------------------- |
| Metadata Mongo (`buckets`, `namespaces`)          | `db_name` / `bucket_id`+`namespace_name`    | drop bucket + its ns rows   | drop one namespace row                 |
| Doc-store Mongo (alias = `db_name`): `RefDoc`     | `namespace` field                           | drop whole DB               | delete RefDocs where `namespace == ns` |
| Milvus, collection = `db_name`                    | partition = `hash(namespace)` **(shared!)** | drop the collection         | delete **by metadata filter**          |
| S3 / data lake, container = `bucket_name`         | object prefix = `folder_name/`              | delete all objects + bucket | delete objects under `folder/` prefix  |
| Dagster dynamic partitions                        | composite key `{bucket}\|{uri}`             | orphaned once un-enumerated | reconciled by next observe             |
| Permissions (`RoleEntity.access_rules`, ceilings) | `aihub.[user\|admin].knowledge.{db}.{ns}`   | purge `...knowledge.{db}.>` | purge `...knowledge.{db}.{ns}`         |

Three constraints shaped the design:

1. **The pipeline is the single writer** of the doc store and vector store. Document deletion is already
   pipeline-mediated (the API deletes the S3 file and publishes `SourceUpdatedEvent`; the observe→remove chain
   reconciles the stores). A second writer racing in-flight ingestion runs must be avoided.
2. **The API cannot do the heavy work synchronously.** Production runs `gunicorn -w 1 --timeout=300`
   (`packages/api/Dockerfile`). A synchronous purge of thousands of documents would blow the worker timeout
   mid-operation (leaving a half-deleted database) and, with one worker, freeze the whole API while it ran. Only S3
   object deletion is O(N) (each document fans out into parsed markdown + extracted figure objects); the Milvus
   drop-collection, Mongo `dropDatabase`, `delete_many(namespace==ns)`, and Milvus filtered-delete are single
   server-side calls.
3. **Namespaces share Milvus partitions.** Namespaces are hashed into 1023 shared partitions
   (`milvus_partition_manager.py`, "collisions acceptable since queries filter by namespace"). Namespace vector cleanup
   must therefore be a metadata-filtered delete, never a partition drop.

## Decision Drivers

- **Durability.** A destructive multi-store teardown must survive an API or pipeline restart. Dagster runs are
  persisted, retriable, and observable (the run-failure notification sensor already exists); an in-process FastAPI
  background task is none of these.
- **Fast, bounded API responses.** The request that starts a deletion must return in milliseconds regardless of corpus
  size, and must never freeze the single API worker.
- **Preserve the single-writer invariant.** The doc store and vector store must keep exactly one writer to avoid races
  with in-flight ingestion.
- **Correctness of shared Milvus partitions.** Deleting namespace A must never delete namespace B's vectors when they
  hash to the same partition.
- **Re-ingestion after re-upload must be guaranteed** — deleting a database and later re-uploading the same file must
  re-ingest it, not skip it as "already materialized".

## Decision

**Deletion is an asynchronous "mark-then-sweep": a fast O(1) API call flips a soft-delete flag, and a Dagster teardown
job driven by that flag does the heavy multi-store purge and hard-deletes the rows as its final step.**

- **`202 Accepted`, synchronously O(1).** `DELETE /databases/{database}` and
  `DELETE /databases/{database}/namespaces/{namespace}` revoke the resource's access rules and roles, flip a new boolean
  `deleting` flag on the `BucketEntity` / `NamespaceEntity`, and return `202`. Milliseconds regardless of corpus size.
  Revocation happens here rather than in the job so the teardown never touches the auth collections; it is best-effort,
  because a stale rule must not be able to block a deletion.

- **The `deleting` flag is the tap-shutoff.** Every enumeration path — `get_databases`, the per-bucket observe schedule,
  and the NATS document-uploaded sensor — excludes `deleting` rows, so ingestion stops immediately *and* the in-flight
  ingestion race is resolved (a bucket marked `deleting` is simply never routed). The row survives, flagged, long enough
  for the teardown job to read `db_name` / `bucket_name` / `folder_name`; it is hard-deleted only as the job's final
  step. The teardown sensor is the one enumerator that deliberately does **not** exclude `deleting` rows — they are
  precisely its work queue.

- **The flag is the request; there is no teardown event.** The teardown sensor enumerates the rows flagged `deleting`
  and derives the run entirely from them — every field the job needs (`db_name`, `bucket_name`, `folder_name`, the ids)
  already lives on the entity, and the partition-registry name is ingestor-derived, so an event would carry nothing the
  database does not already hold.

  This replaces an earlier design in which the API published a `KnowledgeTeardownRequestedEvent` to its own JetStream
  stream. That design had a durability hole precisely where the ADR claimed durability: the flag was set *before* the
  publish with no rollback, so a publish failure stranded the row immediately; and the sensor acked each event before
  Dagster had persisted the run request, so a daemon crash in that window lost it. Nothing re-drove either case —
  ingestion self-heals through the nightly observation, but teardown had no timer at all — leaving a permanently
  `deleting`, UI-hidden database whose stores were never purged. Reading the flag makes the sensor convergent instead:
  whatever is still flagged is still owed, so no message can be lost, and the dedicated stream, its consumer and the
  event type all disappear.

  **Re-drive after failure.** Dagster deduplicates run keys forever, so keying on the entity id alone would make a
  failed teardown unretryable. The sensor instead tags each request with its target id and numbers the run key by how
  many runs that target has already had: the key stays stable while an attempt is pending (repeated ticks re-request it
  and Dagster drops the duplicate) and moves on once that attempt has finished, which is exactly when a retry is wanted.
  On success the row is hard-deleted, so the target stops being enumerated at all.

- **The Dagster teardown job owns the heavy work**, in a fixed, idempotent order so a failed run is "retry until clean"
  with a visible failed run rather than a silent half-deletion:

  - *Database*: drop the Milvus collection → drop the doc-store Mongo database → delete all S3 objects + the bucket →
    (optional) purge orphaned `{bucket}|*` dynamic partitions → hard-delete the namespace rows + bucket row.
  - *Namespace*: delete S3 objects under `folder_name/` → delete RefDocs where `namespace == ns` → delete Milvus vectors
    by metadata filter `namespace == ns` (**never** a partition drop) → hard-delete the namespace row.

- **Re-ingestion does not depend on partition purge.** A re-uploaded file re-ingests via the existing
  mtime-in-`DataVersion` workaround: the re-materialization signal is `DataVersion = f"{updated}-{hash}"` where
  `updated` is the S3 `LastModified` (server-set at upload). A re-upload always lands strictly later than the original
  ingest (a deletion sits between them), so `DataVersion` changes and `AutomationCondition.eager()` re-materializes —
  even for byte-identical content. This is a deliberate workaround for Dagster OSS lacking a partition-wipe API
  ([#14749](https://github.com/dagster-io/dagster/issues/14749): `wipe_asset_partitions` is Dagster+ only): because
  `delete_dynamic_partition` does not clear per-partition materialization/data-version memory, re-ingestion cannot rely
  on purging.

- **Partition purge is optional hygiene, not correctness.** It runs only for database deletion, where the bucket stops
  being enumerated and its `{bucket}|*` keys would otherwise sit orphaned in the shared registry forever (the
  registry-bloat that #14749 itself cites). Namespace deletion needs no purge — the next observe run reconciles the
  folder's keys away once the S3 files are gone.

- **Guards (all `403`).** `auto_sync` databases (SharePoint/OneDrive-fed) are refused — their source pipeline would just
  re-sync them. Legacy `default_rag` / `shared_rag` buckets are refused — they are bound to a deploy-time pipeline.
  Mongo-internal / main-db names are refused at the controller via the existing reserved-name guard.

- **Frontend.** A destructive confirm dialog requires the admin to type the database/namespace name and shows the
  document count; on `202` the databases query is invalidated and, because `get_databases` now hides `deleting` rows,
  the item disappears immediately.

**Permission-rule purge (step 6 above) is deferred to a phase 2** — the teardown removes the stores and rows; stale
`aihub.*.knowledge.{db}.>` rules on roles / tenant ceilings are a follow-up.

## Consequences

### Positive

- The API request is O(1) and never freezes the single worker; deletion of an arbitrarily large corpus starts in
  milliseconds.
- The destructive work is durable, retriable, and observable (persisted Dagster runs + the existing run-failure
  notification sensor); an API or pipeline restart cannot leave the teardown half-done and forgotten.
- The pipeline stays the single writer of the doc and vector stores; the `deleting` tap-shutoff removes the in-flight
  ingestion race by construction.
- Shared Milvus partitions are safe: namespace cleanup is a metadata-filtered delete, so colliding namespaces are never
  collateral damage.
- Re-uploading a deleted file re-ingests reliably, without depending on a partition-wipe API the OSS runtime does not
  have.

### Trade-offs

- **Deletion is eventually-consistent, not immediate.** The `202` means "scheduled"; the corpus is purged shortly after
  by the teardown job. The UI hides the item at once, but the underlying stores are freed asynchronously.
- **A soft-delete state now exists on two entities.** Every current and future enumeration path must remember to exclude
  `deleting` rows; the teardown sensor is the deliberate exception. A missed exclusion would re-expose a database that
  is being torn down.
- **One more sensor per pipeline.** Teardown adds a sensor that queries the flagged rows every 30 s. It costs one
  indexed database read per tick and no NATS traffic at all — the earlier event-driven design added a JetStream stream
  and consumer *per knowledge database* instead.
- **Only the rules the platform granted are revoked.** Deletion removes the per-resource rules and roles that creation
  granted, but a rule an operator wrote by hand — a broader wildcard, or one on a differently-named role — is left
  alone, since the platform cannot tell an intentional grant from a leftover.
