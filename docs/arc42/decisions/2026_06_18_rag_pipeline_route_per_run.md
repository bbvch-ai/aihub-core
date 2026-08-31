# Generic Document Ingestion Pipeline: one deployment, all knowledge databases (collection-per-db, route-per-run)

## Context

Historically each knowledge database was bound 1:1 to a Dagster pipeline at deploy time. Adding a database required a
new `app/` module, Dockerfile, compose service, `compose-config.yml` entry, `workspace.yml` code-location, and bucket
env var — so only two existed (`default_rag_pipeline`, `shared_rag_pipeline`). Users could not create a knowledge
database from the UI without a redeploy.

The data model was already the right shape: `BucketEntity` is the source of truth (its `bucket_name` is the S3
container, its `db_name` is the Milvus collection and Mongo store, 1:1), `BucketEntity.get_all_buckets()` exists, and
the API already enumerates all databases at runtime. The blocker was purely in the pipeline, which baked a single
`datalake_container_name` into its asset keys, partition names, resources, jobs, and NATS topic.

A "knowledge database" is a `BucketEntity`; "folder"/"namespace" is a `NamespaceEntity` row; a chunk carries `namespace`
\+ `document_id` but no `db` field — database identity is simply *which Milvus collection it lives in*.

**Scope: Stage 2 only.** "document ingestion pipeline" here means the data lake → vector store stage (parse, chunk, embed, index). The
Stage 1 source connectors (SharePoint, rclone, local filesystem → data lake) are unchanged and remain per-source, and a
deployment is still free to build its own Stage 1 + Stage 2 pipeline for its own bucket. This decision is about how
knowledge databases are *ingested from the data lake*, not about how documents get into it.

## Decision Drivers

- *Self-service*: users must create knowledge databases from the UI with no deployment.
- *One pipeline, many databases*: exactly one deployed ingestion pipeline of a given type should ingest all databases it owns,
  reading their configs from MongoDB at runtime.
- *Isolation preserved*: each database keeps its own vector collection and document store.
- *No disruption / no reprocessing*: the existing `default`/`shared` databases must keep ingesting and serving
  unchanged, with no re-parse/re-embed of existing corpora.
- *Coexistence*: a new dynamic pipeline must run alongside the legacy fixed pipelines without double-ingesting their
  data.

## Alternatives Considered

1. **Migrate the legacy pipelines onto the new route-per-run model and delete their scaffolding.** Rejected: changing
   partition keys (`file` → `{bucket}|{file}`) and dropping the container prefix from asset keys makes Dagster treat
   every existing partition as new, forcing a full re-parse (MinerU) + re-embed of all existing corpora. Upsert-safe but
   an avoidable one-time compute cost and risk.
2. **Dynamically merge N `Definitions` (one per bucket) at code-load time**, reloading the code location when a bucket
   is added. Rejected: the asset graph would change on every bucket creation, requiring code-location reloads and
   per-bucket sensor/asset-name namespacing; far more moving parts than routing per run.
3. **A true `MultiPartitionsDefinition` with `(bucket, file)` dimensions.** Rejected: Dagster permits at most one
   *dynamic* dimension, and both bucket and file are dynamic. The composite key is therefore encoded into a single
   `DynamicPartitionsDefinition` key string instead.
4. **A single wildcard NATS sensor** subscribing to `pipeline.datalake.*.to.knowledge.*.*.*.*` and filtering the
   received events by the bucket's `ingestor`. Rejected: a JetStream stream for that wildcard subject would *overlap*
   the legacy pipelines' per-instance streams, and JetStream forbids overlapping subjects between streams — creating it
   would break `default`/`shared` ingestion. This constraint is what drove the subject grammar in decision 7: the
   overlap comes from reusing the legacy `datalake` source token, not from wildcarding as such.

## Decision

Add a new, **additive** `document_ingestion_pipeline` that ingests all knowledge databases tagged for it, and leave the legacy
pipelines untouched.

1. **`ingestor` field on `BucketEntity`** (`unassigned` / `default_rag` / `shared_rag` / `document_ingestion`) records which deployed
   pipeline owns a database. It is the routing guard that lets the new pipeline coexist with the legacy ones. The
   startup seeder labels the two managed buckets `default_rag`/`shared_rag`.

   **The field default is the inert `unassigned`, and this is load-bearing for upgrades.** Rows written by releases
   predating the field have no `ingestor` key, and MongoEngine applies the *field default* when the key is absent — so
   defaulting to `document_ingestion` would make every knowledge database in an upgraded deployment read as owned
   by the document ingestion pipeline,
   which would then claim it and re-parse + re-embed its entire corpus alongside the deploy-bound pipeline that already
   owns it. The seeder cannot be relied on to repair this: it only touches the two buckets it seeds, it is skipped
   entirely when `CREATE_DEFAULT_BUCKETS` is off, and the pipeline's sensors do not wait for it. Deployments with
   additional buckets and their own pipelines therefore would not be covered at all. With an inert default, an
   un-migrated row is owned by nobody, the legacy pipelines keep working (they never read `ingestor`), and **no
   migration script or operator action is required on upgrade**. The same default protects
   `bucket_utils._get_or_create_bucket`, the path by which any pipeline auto-registers a bucket row it does not find.

2. **Self-service create-database** API (`POST /knowledge/databases/{database}`, gated by `aihub.admin.knowledge` —
   the knowledge root, since the database being created does not exist yet to be named by a rule) and UI, mirroring the
   existing create-namespace flow. No deployment required. Creation grants the creator and their tenant admin on the
   new database, and deletion revokes it; see ADR `2026_06_15_auto_grant_creator_access_to_agent_instances`.

3. **The user selects the ingestor at creation time**, rather than it being assigned implicitly. The choice is offered
   as a **server-provided, localized list** (`GET /knowledge/ingestors`), not a
   client-side enum: the set of pipelines a database may be assigned to is a platform fact, so the API owns it and the
   UI renders whatever it is given. `create_database` rejects a non-selectable ingestor with a 400.

   Only `document_ingestion` is selectable out of the box. `default_rag`/`shared_rag` are deliberately **excluded**: each is bound to a
   single bucket by an env var at deploy time, so a database assigned to one of them would be silently never ingested.
   They exist as `ingestor` values only to mark the legacy buckets for the routing guard.

   A selector with one built-in option is intentional. When a second pipeline *type* is deployed (a different chunking
   strategy, an OCR-heavy variant, a tenant-specific pipeline), the database must record which one owns it — and that is
   a user's choice, not an implicit default.

   **Extending the selectable set — the pipeline registers itself.** A customer-specific deployment makes its own
   route-per-run pipeline selectable *without forking the platform*: it passes `display_name` and `description`
   alongside its `ingestor` to `document_ingestion_pipeline_definitions`, and a sensor in that pipeline upserts an `IngestorEntity`
   row. `GET /knowledge/ingestors` and `create_database` read that collection, so the ingestor is offered as soon as
   the pipeline is deployed. No `IngestorType` change, no API contract change, no SDK regeneration.

   The registration goes through the database rather than through the API's own process because the two are separate
   containers. An in-memory registry, or one populated from Python entry points, is only ever visible to the process
   that holds it — so a custom ingestor would appear only if the customer's package were also installed into the *API*
   image, a coupling that is invisible and fails silently: deploy the pipeline, forget the API image, and the ingestor
   simply never shows up. Mongo is infrastructure both sides already share, and it mirrors how ownership is resolved in
   the other direction (which buckets an ingestor owns is a runtime `BucketEntity` query). Registering from a sensor
   rather than at import means a momentary database outage cannot take a code location down, at the cost of the
   ingestor appearing one sensor tick after deployment.

   Two consequences worth stating: labels are **required** for a custom ingestor (an unlabelled one could only render
   as a bare id in the selector), and re-registration is **last-writer-wins**, so a redeploy carrying changed labels
   updates them rather than erroring.

   **Why the wire field is a plain `str`, not the `IngestorType` enum.** The `ingestor` value on the request/response
   DTOs — and therefore in the OpenAPI schema and generated SDK — is deliberately a free string. Typing it as the closed
   `IngestorType` enum would bake the platform's fixed set into the API contract and the SDK, making a custom,
   deployment-registered ingestor *unrepresentable on the wire*: a client validating against the enum would reject it,
   defeating the whole mechanism. The selectable set stays authoritative and server-owned, but it is discovered at
   runtime via `GET /knowledge/ingestors` instead of frozen into a type. `BucketEntity.ingestor` likewise carries no
   static `choices` — `create_database` validates the submitted value against `IngestorEntity`, and because routing is
   exact-match a value owned by no pipeline is simply never ingested. `IngestorType` remains an enum
   internally for the platform's own values (defaults, the routing guard, the seeder); only the boundary is a string.

4. **One Milvus collection per database, routed per run.** The bucket/db becomes a run/partition dimension via a
   composite partition key `{bucket}|{encoded_file_uri}` in a single shared `DynamicPartitionsDefinition`. IO managers
   and ops resolve `container_name`/`store_name` per run instead of from constructor config. One file still maps
   to one Dagster partition. (`|` is a safe separator because `BucketEntity` already constrains bucket names to
   `^[a-zA-Z][a-zA-Z0-9]*$` — a leading letter is also required so the name is a valid Milvus collection.)

   **Routing uses two different mechanisms, chosen by how the run was triggered — this is the central correctness
   constraint of the design.** Dagster's `InitResourceContext` exposes *neither* the partition key *nor* custom run tags
   for auto-materialized runs, so a resource cannot resolve its own target bucket. That is why nothing bucket-scoped is
   a resource at all: the stores are built from `store_builders`, keyed by a bucket that each op and IO manager resolves
   from its own context. Therefore:

   - **Partitioned write path** (`documents` / `nodes` / `summary_nodes`, launched by the automation sensor, which
     supplies only a composite partition key): routes on the **partition key**, inside the IO managers and inside the
     two nodes ops that touch the stores directly.
   - **Observe and remove path** (launched by our schedule, NATS sensor, or run-after-success sensor): routes on the
     `aihub/bucket` run tag, read from the op's own `OpExecutionContext`. The remove run is non-partitioned, so the S3
     IO manager's non-partitioned branch reads the tag too — which is why the run-after-success sensor must propagate
     the bucket tag from the observe run to the remove run.

   Collapsing the two *signals* into one is not possible without changing Dagster's resource-init contract. What is
   collapsed is the store construction behind them: both paths end at `store_builders`, so there is one factory and one
   `context → bucket → store` resolution shape rather than a resource seam beside a direct-call seam.

   `InputContext` — unlike `OpExecutionContext` — still exposes no public run-tags accessor, so the IO managers read
   Dagster's non-public `step_context`. That reliance is pinned by a test that fails if a Dagster upgrade removes it,
   rather than being discovered when a remove run routes nowhere.

5. **Bucket-scoped partition reconciliation.** `replace_partition_keys_for_bucket` only diffs the current bucket's
   subset of keys within the shared registry, so one bucket's observe run cannot delete another bucket's partitions —
   eliminating the class of bug latent in the old global `rclone_partitions` name.

6. **Every deployment-global name is derived from the `ingestor`.** Asset keys (`{ingestor}_datalake_to_vectorstore/…`),
   the dynamic-partition registry (`{ingestor}_document_partitions`), the job names, and the Dagster intermediates
   prefix all carry the ingestor. Asset keys are unique per Dagster *deployment* and `DynamicPartitionsDefinition` names
   are global to the Dagster *instance*, so hardcoding them would mean a second pipeline type (the very thing the
   ingestor selector exists to allow) could not be deployed alongside the first — two code locations would claim the
   same asset keys and share one partition registry. Deriving them costs nothing and keeps the factory instantiable more
   than once.

   This is also what keeps a customer's own bespoke pipeline out of the way: a deployment that builds its own Stage 1 +
   Stage 2 via `default_definitions(datalake_container_name="pocrag")` gets `["pocrag", "datalake_to_vectorstore", …]`
   asset keys and a `pocrag_document_partitions` registry, which cannot collide with the document ingestion pipeline's.

7. **One ingestor-keyed JetStream stream, fanned out per bucket in the sensor.** Uploads are published on
   `pipeline.{ingestor}.{bucket}.to.knowledge.{db}.…` — the same nine-token grammar as before, with the *ingestor*
   rather than `datalake` in the source-type position. A pipeline therefore owns exactly one stream
   (`pipeline.{ingestor}.>`) and one durable consumer, however many databases it serves, and cannot overlap the legacy
   `pipeline.datalake.…` streams because the type token differs. The sensor drains that stream once per tick, groups
   the batch by the bucket in the subject, and decides per database; the schedule still enumerates
   `BucketEntity.get_all_buckets()` filtered by `ingestor`.

   The alternative — one stream per bucket, keyed source→target like legacy — was implemented first and abandoned:
   streams, consumers and per-tick NATS round-trips all grew linearly with the number of knowledge databases, for no
   fundamental reason. Two pipeline *types* never react to the same upload, so type-keyed subjects never need to
   overlap by construction. Existing deployments that ran the per-bucket shape keep orphaned
   `pipeline_datalake_*_knowledge_*` streams; nothing consumes them and they can be removed with `nats stream rm`.

   **Cluster safety.** Sensors evaluate only on the Dagster daemon, which is a singleton — running more than one is
   unsupported — and every request carries a run key Dagster deduplicates, so a bucket cannot be observed twice
   concurrently. Neither is load-bearing for correctness anyway: an observation is a full reconciliation of the bucket,
   so a duplicate trigger converges to the same state and a lost one is picked up by the next upload or the daily
   schedule. This is why a durable pull consumer suffices here, unlike agent control events, which are state
   transitions needing exactly-once delivery.

### Naming

The pipeline is the **Generic Document Ingestion Pipeline**. It parses, chunks, embeds and indexes documents into a
vector store; it performs no retrieval and no generation, so naming it after RAG would describe the wrong stage. The
RAG *agent* is what does retrieval-augmented generation and is named accordingly.

"Generic" is a display-only adjective. Identifiers use `document_ingestion_pipeline`
(`document_ingestion_pipeline_definitions`, `DocumentIngestionPipelineSettings`, `DOCUMENT_INGESTION_*`,
`app.document_ingestion_pipeline`) and the ingestor routing id is `document_ingestion`, because
`generic_document_ingestion_pipeline` buys nothing and lengthens every NATS subject and asset key that embeds it.

The frozen `default_rag` / `shared_rag` ingestor ids and the `default_rag_pipeline` / `shared_rag_pipeline` image names
are deliberately excluded from this naming: they identify images that will never be rebuilt and that existing
deployments still pull by those exact tags. This ADR's own filename likewise keeps its original slug — ADR filenames
are dated records, and renaming them breaks inbound links for no gain.


## Consequences

### Positive

- Knowledge databases are created self-service from the UI with no redeploy, no new code location, compose service, or
  env var.
- Existing `default`/`shared` databases are completely unaffected: no migration, no reprocessing, no risk.
- Upgrading a deployed setup needs no data migration: pre-existing bucket rows read the inert `unassigned` default and
  are claimed by no pipeline.
- Per-database isolation is preserved (one collection + one document store per database).
- The shared-registry partition bug class is fixed by bucket-scoped reconciliation.
- Bespoke customer pipelines (their own Stage 1 + Stage 2, independent of the knowledge base) keep working untouched:
  their buckets are `unassigned`, and their asset keys, partition registries, job names, and Dagster intermediates
  prefix are all namespaced by their own container name.
- A second pipeline *type* can be deployed alongside the first, because every deployment-global name is ingestor-scoped.
- A customer-specific pipeline becomes user-selectable without forking the platform: passing `display_name` and
  `description` to `document_ingestion_pipeline_definitions` is enough — the pipeline registers itself in the database the API reads,
  so no `IngestorType` change, no API-contract change, no SDK regeneration, and nothing to install into the API image.

### Trade-offs

- The `ingestor` field is a plain `str` at the API boundary (request/response DTOs, OpenAPI, SDK) rather than the typed
  `IngestorType` enum. This is what lets a deployment-registered custom ingestor travel on the wire, but the SDK client
  gets a string instead of a discriminated union, so the frontend does not get compile-time validation of ingestor
  values — it relies on the server-provided `GET /knowledge/ingestors` list and server-side validation instead.

- The two legacy fixed deployments remain; the per-database deployment scaffolding is not removed (it is simply no
  longer needed for new databases). This is a **deliberate deviation** from the originating issue, which asked to
  migrate `default`/`shared` onto the shared pipeline and delete their scaffolding. That migration is deferred to a
  separate change because it is not free: the legacy asset keys are container-prefixed and their partition keys are bare
  file URIs (vs. `{bucket}|{uri}`), so Dagster would see every already-ingested document as new and re-parse (MinerU) +
  re-embed both corpora in full. The run is upsert-safe and non-destructive — same collection names, vectors overwrite
  by `uri_to_id`, retrieval keeps working throughout — but it is hours of avoidable compute that should be scheduled
  deliberately rather than triggered as a side effect of merging a feature. Rollback for that future change is to flip
  `ingestor` back and redeploy the legacy code locations.

- Three `ingestor` values exist while only one is selectable, which reads as redundancy until the legacy pipelines are
  retired. The alternative — omitting the field and inferring ownership from a bucket name allowlist — would bury the
  routing rule in the pipeline instead of the data model.

- The document ingestion pipeline runs one asset graph shared across all its databases — one process, one resource pool, one crash
  domain — rather than the per-database isolation the legacy deployments have. Acceptable at expected scale; the
  per-tick enumeration of buckets is the scaling limit to watch.

- IO managers resolve the store per run (a cheap idempotent Mongo lookup, cached per run), trading a little runtime work
  for deploy-time flexibility.
