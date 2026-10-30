# packages/pipeline - Data Ingestion & Processing SDK

**Purpose**: Dagster-based SDK for document ingestion, parsing, embedding generation, and vector storage. Three parts:
the framework (`packages/pipeline/`), deployable pipeline apps (`app/`), and playground examples (`playground/`).
Prepares data for RAG agents — agents query the output (Milvus vectors, MongoDB documents), they don't use this SDK
directly. External sources are configured per knowledge database from the UI, not per deployment.

## Folder Structure

```
packages/pipeline/                        # SDK framework
├── swiss_ai_hub/pipeline/
│   ├── assets/factories/                  # Asset factory functions (core building blocks)
│   │   ├── data_lake_to_vector_store/     # Stage 2: documents, nodes, summary_nodes, removed_documents
│   │   ├── source_to_data_lake/           # Stage 1 generic: data_lake_file, placeholder_refdocs, removed_data_lake_files + routed_* (bucket per run)
│   │   ├── share_point_to_data_lake/      # Stage 1: observable_share_point
│   │   ├── rclone_to_data_lake/           # Stage 1: observable_rclone (routed by run tag)
│   │   ├── structured_to_data_lake/       # Stage 1: structured_sync_factory — sync → list → reconcile → delete → announce
│   │   └── local_files_system_to_data_lake/  # Stage 1: observable_local_file_system
│   ├── io/                                # I/O managers (storage handlers)
│   │   ├── s3_data_lake_io_manager.py      # S3/MinIO/SeaweedFS (Stage 1, one bucket)
│   │   ├── azure_data_lake_io_manager.py   # Azure Data Lake Storage (Stage 1)
│   │   ├── doc_store_io_manager.py         # MongoDB document store (Stage 1, one db)
│   │   ├── routed_s3_data_lake_io_manager.py # Stage 2: bucket resolved per run
│   │   ├── routed_doc_store_io_manager.py  # Stage 2: doc store resolved per run
│   │   ├── vector_store_io_manager.py      # Stage 2: Milvus, collection resolved per run
│   │   ├── ingestion_marking.py            # mark_ref_docs_as_ingested() — shared is_ingested flip
│   │   ├── share_point_io_manager.py       # SharePoint (read-only)
│   │   ├── routed_rclone_io_manager.py     # Rclone source pipeline: remote resolved per run (read-only)
│   │   └── local_file_system_io_manager.py # Local/network filesystem (read-only)
│   ├── ops/                               # Operations (@op processing steps)
│   │   ├── data_lake/                     # Parsing, versioning, figure descriptions, table refinement
│   │   ├── document/                      # RefDoc insertion, cleanup, metadata, placeholders, markdown frontmatter
│   │   ├── nodes/                         # Chunking, embedding, vector insertion, summaries
│   │   ├── rclone/                        # data_version_by_partition_for_rclone_files (composite keys)
│   │   ├── structured/                    # Structured source steps (op factories per source): sync via dlt, list, reconcile
│   │   ├── source/routed/                 # Source pipeline write/remove path: bucket-routed data lake ops + announce
│   │   ├── teardown/                      # knowledge_teardown_op (database / namespace teardown)
│   │   └── repair/                        # repair_orphaned_nodes_op (manual cleanup of stranded vector nodes)
│   ├── resources/                         # External dependencies (ConfigurableResource subclasses)
│   │   ├── data_lake/base/                # AbstractDataLakeClient, AbstractDataLakeClientResource
│   │   ├── data_lake/s3/                  # S3DataLakeClient, S3DataLakeFileSystemResource
│   │   ├── data_lake/azure/               # AzureDataLakeClient, AzureDataLakeFileSystemResource
│   │   ├── parser/                        # DocumentParserResource, MarkdownStructuralNodeParserResource, etc.
│   │   ├── vector_store/                  # MilvusVectorStoreResource
│   │   ├── doc_store/                     # MongoDocumentStoreResource
│   │   ├── llm/                           # EmbeddingModelResource, LanguageModelResource
│   │   ├── share_point/                   # SharePointResource (MS Graph API)
│   │   ├── rclone/                        # RcloneClient (RC API; stateless, built per run)
│   │   ├── structured/                    # Structured sources: dlt destination (markdown records + referenced files), per-database dlt state store
│   │   ├── jira/                          # JiraClient (dlt RESTClient: Cloud + Data Center search, comments, preflight calls)
│   │   ├── confluence/                    # ConfluenceClient (dlt RESTClient: REST v1 CQL search), next-link paginator, error
│   │   ├── mediawiki/                     # MediaWikiClient (dlt RESTClient: action API, continue paging), sign-in, error
│   │   ├── local_file_system/             # LocalFileSystemResource
│   │   └── factory.py                     # Resource factory functions (assembles resource dicts)
│   ├── sensors/
│   │   ├── factory.py                     # default_automation_sensor (auto-materialization)
│   │   ├── run_after_success_sensor.py    # Chain a job after another job's successful run
│   │   ├── run_failure_notification_sensor.py # Apprise alerts on any failed run
│   │   ├── ingestor_registration_sensor.py # Announce this pipeline: labels + configuration form + schema
│   │   ├── source_pipeline_registration_sensor.py # Stage-1 counterpart: announce a source pipeline (+ shared id/label gate)
│   │   ├── source_bucket_cleanup_sensor.py # Forget databases a source pipeline no longer fills (partitions + remote)
│   │   ├── knowledge_teardown_sensor.py   # Run teardown for databases/folders flagged `deleting`
│   │   ├── single_flight_run_guard.py     # "Is a run of this job already queued or running?"
│   │   └── nats/
│   │       ├── nats_document_uploaded_sensor.py  # NATS event-driven triggers
│   │       ├── consumed_event_batch.py           # Drains the JetStream backlog, defers acks
│   │       ├── observation_sensor_cursor.py      # Sensor state carried between ticks
│   │       ├── observation_run_decider.py        # Pure request-or-wait decision
│   │       ├── observation_run_history.py        # Run-tag lookups the cursor cannot hold
│   │       └── per_bucket_observation_sensor_cursor.py  # One cursor slot, one state per database
│   ├── ingestors/
│   │   └── document_ingestion_config.py   # DocumentIngestionConfig: the announced per-database form (Form duality)
│   ├── source_pipelines/
│   │   ├── rclone_sync_config.py          # RcloneSyncConfig: the announced per-database source form (six backends)
│   │   ├── structured_sync_config.py      # StructuredSyncConfig: source kind + one option group per kind
│   │   ├── jira/                          # The Jira kind: options form, preflight, issue → markdown file
│   │   ├── confluence/                    # The Confluence kind: options, preflight, page → markdown file, storage → markdown
│   │   ├── mediawiki/                     # The MediaWiki kind: options, preflight, scope, page → markdown file, file → reference, HTML → markdown
│   │   ├── structured_file_unavailable_error.py  # A file the source will not serve: skipped, tried again next run
│   │   └── abstract_structured_source_adapter.py  # Contract per structured source kind: dlt source, record → file, read_file
│   ├── services/
│   │   ├── knowledge_teardown_service.py  # Destroys a database/namespace across every store
│   │   ├── default_partition_repair_service.py # Provisions the collection, moves nodes stranded in `_default`
│   │   └── orphaned_node_repair_service.py # Deletes vector nodes whose document has no record and no file
│   ├── schedules/factory.py               # daily_schedule_at, default_daily_materialize_schedule
│   ├── jobs/factory.py                    # observe_source_job, materialize_asset_job, materialize_all_job
│   ├── jobs/knowledge_teardown_job.py     # {ingestor}_knowledge_teardown
│   ├── jobs/repair_orphaned_nodes_job.py  # {ingestor}_repair_orphaned_nodes (manual, dry run by default)
│   ├── executors/factory.py               # default_process_executor (in-process)
│   ├── automation/all_deps_completed.py   # AutomationCondition for all-deps-ready
│   ├── types/                             # Domain types (Pydantic models)
│   │   ├── data_lake_file.py              # File in cloud storage (S3 bucket)
│   │   ├── ref_doc_document.py            # Parsed document (extends LlamaIndex Document)
│   │   ├── source_file.py                 # Generic source file interface + MinimalSourceFile
│   │   ├── markdown_frontmatter.py        # MarkdownFrontmatter: a .md file's YAML block → document fields + metadata
│   │   ├── malformed_frontmatter_error.py # The block is not a YAML mapping → file ingested as written
│   │   ├── share_point_file.py            # SharePoint-specific file
│   │   ├── rclone_file.py                 # Rclone-specific file (70+ cloud backends)
│   │   ├── rclone_remote.py               # How a run addresses one database's remote (name, fs, patterns)
│   │   ├── structured_record_file.py      # One API record as a markdown file: namespace, frontmatter, body
│   │   ├── structured_file_reference.py   # A binary file a source offers: key, download URL, title and link
│   │   ├── structured_source_state.py     # dlt state + scope fingerprint kept per database between syncs
│   │   ├── structured_sync_outcome.py     # Sync → listing handover: written keys + fingerprint, never secrets
│   │   ├── structured_listing.py          # Listing → reconcile handover: listed keys + written keys
│   │   ├── default_partition_repair_report.py # What a `_default` repair moved and deleted
│   │   └── figure_metadata.py             # Image/figure metadata
│   ├── util/                              # Utilities
│   │   ├── document_ingestion_definitions_util.py         # document_ingestion_pipeline_definitions() — Stage 2, route-per-run (CRITICAL)
│   │   ├── rclone_pipeline_definitions_util.py            # rclone_pipeline_definitions() — Stage 1 source pipeline, route-per-run
│   │   ├── structured_pipeline_definitions_util.py        # structured_pipeline_definitions() — Stage 1 dlt source pipeline, route-per-run
│   │   ├── definitions_util.py            # Stage 1 deploy-time builders (SharePoint via MS Graph, local FS)
│   │   ├── id_utils.py                    # uri_to_id() — URI to document ID (MD5 hash)
│   │   ├── partition_utils.py             # replace_partition_keys(), composite {bucket}|{uri} keys
│   │   ├── run_routing.py                 # BUCKET_RUN_TAG, bucket_from_run_tag/_partition_key, owned_by_ingestor/_source (CRITICAL)
│   │   ├── store_builders.py              # build_vector_store/doc_store/s3_client for a bucket
│   │   ├── source_builders.py             # source_config_for_bucket, rclone_remote_for_bucket — per-run source resolution
│   │   ├── source_updated_notifier.py     # notify_source_updated() — SourceUpdatedEvent per written/removed file
│   │   ├── model_builders.py              # Per-database configuration: models, enrichment flags, vector width
│   │   ├── bucket_utils.py                # get_db_name_from_bucket_name() — S3 bucket → MongoDB name
│   │   ├── key_utils.py                   # group_name_from_asset_key() — asset group derivation
│   │   └── meta_utils.py                  # data_lake_metadata_table() — Dagster UI formatting

app/                                   # Deployable pipelines (Dagster gRPC code locations)
├── document_ingestion_pipeline/        # THE document ingestion pipeline — one deployment, all self-service knowledge DBs
│   ├── __init__.py                    # defs = document_ingestion_pipeline_definitions()  (route-per-run, no bucket env var)
│   └── Dockerfile                     # dagster api grpc on port 4000; rclone_pipeline/Dockerfile is the same file with another PIPELINE default
├── rclone_pipeline/                    # THE rclone source pipeline — one deployment, every database whose source is `rclone`
│   ├── __init__.py                    # defs = rclone_pipeline_definitions()  (route-per-run, no source env vars)
│   └── Dockerfile                     # copy of the ingestion Dockerfile with PIPELINE=rclone_pipeline (release workflow builds app/<name>/Dockerfile)
└── structured_pipeline/                # THE structured source pipeline — API records (Jira, Confluence, …) as markdown, via dlt
    ├── __init__.py                    # defs = structured_pipeline_definitions()  (route-per-run, no source env vars)
    └── Dockerfile                     # copy with PIPELINE=structured_pipeline and RUNTIME__DLTHUB_TELEMETRY=false

playground/                            # Examples (START HERE)
├── __init__.py                        # defs = document_ingestion_pipeline_definitions() + a playground BucketEntity
├── structured_demo/                   # Structured source with a `demo_records` kind reading a local JSON file (make structured-demo)
└── quick_start/                       # Tutorials
    ├── simple_pipeline.py             # Hello-world: 2 basic assets, no external deps
    └── my_document_pipeline.py        # Full document ingestion pipeline with all factories
```

## Two-Stage Pipeline Architecture

Source-specific ingestion, then unified processing. This is the core architectural insight.

**Stage 1 (Source → Data Lake)**: An observable asset monitors an external source for changes, downloads files to the
S3-compatible data lake (SeaweedFS). Each file becomes a dynamic partition. A cleanup asset removes orphaned data lake
files when source files are deleted. Stage 1 never touches the doc store or the vector store.

Concrete Stage 1 flows:

- Rclone source pipeline → S3 (`observable_rclone_factory` + the routed `source_to_data_lake` factories): **one
  deployment for every knowledge database whose `BucketEntity.source` is `rclone`**, configured per database from the UI
  (OneDrive/SharePoint, Google Drive, S3, Azure Blob, SFTP, local). See
  [Rclone Source Pipeline](#rclone-source-pipeline-stage-1-configured-per-database).
- Structured source pipeline → S3 (`structured_sync_factory`): API records (Jira, Confluence, …) written as markdown via
  dlt, **one deployment for every knowledge database whose `source` is `structured`**, one run per database. See
  [Structured Source Pipeline](#structured-source-pipeline-stage-1-configured-per-database).
- SharePoint via MS Graph → S3 (`observable_share_point_factory`, deploy-time builder, one bucket)
- Local/network filesystem → S3 (`observable_local_file_system_factory`, deploy-time builder, one bucket)

**Stage 2 (Data Lake → Vector Store)**: Unified pipeline, source-agnostic. All data lake files flow through the same
processing chain regardless of origin:

- `observable_data_lake_factory` → monitors S3 for new/changed files. Before it registers any document partition it runs
  `DefaultPartitionRepairService`: the database's Milvus collection is created with the embedding model's width if
  missing, a half-built one gets its missing partitions, and nodes stranded in `_default` move to their namespace
  partition (#1923). A document partition is what starts an ingestion run, so none meets a half-built collection.
- `documents_factory` → parse (MinerU) → apply a `.md` file's frontmatter → `RefDocDocument` → MongoDB, flagged
  `is_ingested=False` (see [Markdown Frontmatter](#markdown-frontmatter))
- `nodes_factory` → chunk (MD structural) → embed → `TextNode[]` → Milvus, which flips `is_ingested=True`
- `summary_nodes_factory` (optional) → hierarchical summaries → Milvus
- `removed_documents_factory` → cleanup orphaned documents: vector nodes first, then figures, then the MongoDB record.
  The record goes last because it is the only marker of pending work — the next removal run finds the documents to
  remove by their record, so a run that fails at Milvus is retried in full. Every step tolerates an already deleted
  target. Nodes stranded before this order existed (#1925) are cleaned by the `{ingestor}_repair_orphaned_nodes` job
  (see [Repairing Orphaned Vector Nodes](#repairing-orphaned-vector-nodes)).

A document is only reported as ingested — to the API, the UI, and RAG agents — once its nodes are in Milvus. A parsed
document has markdown but no embeddings, so it is not retrievable yet and must not be shown as complete.

## The `document_ingestion_pipeline_definitions()` Function

The primary entry point for creating a Stage-2 pipeline. Located in `util/document_ingestion_definitions_util.py`.
Returns a complete `Definitions` object with all assets, resources, sensors, jobs, and schedules wired together.

**It carries no bucket name.** One deployment serves every knowledge database whose `BucketEntity.ingestor` matches,
resolving the target per run — from the composite partition key `{bucket}|{file_uri}` on the write path, from the
`aihub/bucket` run tag on the observe/remove path. Creating a knowledge database therefore needs no new code location,
compose service, or env var.

```python
defs = document_ingestion_pipeline_definitions(
    ingestor="document_ingestion",  # routing key; namespaces every global Dagster name
    display_name=LocaleString(en="My Pipeline"),  # required for a custom ingestor, defaulted for the platform one
    description=LocaleString(en="What it does"),
    config=None,  # announced form; defaults to DocumentIngestionConfig.as_form(...)
    settings=DocumentIngestionPipelineSettings(),  # per-database DEFAULTS + the observation schedule (see below)
    document_parser_loader_type=LoaderType.MINERU,  # MinerU (default) or DocumentIntelligence
    max_partitions=1000,  # Max partitions added/deleted per tick
)
```

Every deployment-global name — asset keys, the dynamic-partition registry, job names, the Dagster intermediates prefix —
is derived from `ingestor`, because asset keys are unique per Dagster deployment and partition-registry names are global
to the instance. That is what lets a second pipeline *type* be deployed alongside this one.

`settings` is a `DocumentIngestionPipelineSettings` (`DOCUMENT_INGESTION_*`, read from the environment when omitted)
carrying the text, embedding and vision models, the three enrichment flags and the observation schedule. The models and
enrichment flags are **deployment defaults**, not the graph's shape: they pre-fill the form the pipeline announces, and
are what a database that stores no value of its own falls back to at run time. The builder registers them under its
`ingestor` (`model_builders.register_deployment_defaults`), so a run falls back to the settings the pipeline was built
with rather than re-reading the environment: a model named in code wins over the deployment's variables. The asset graph
is identical for every database (`summary_nodes` always exists, and table refinement and figure descriptions are always
in the `documents` graph), and each enrichment op decides per run from the bucket's configuration whether it has work.

Every pipeline built here registers itself: a sensor upserts an `IngestorEntity` carrying labels, form and schema, so
the API's `GET /knowledge/ingestors` can offer it in the create-database dialog and validate what users submit. See
[Making a Custom Pipeline Selectable](#making-a-custom-pipeline-selectable-in-the-ui) for the full mechanism.

Stage-1 counterparts:

- `rclone_pipeline_definitions(...)` in `util/rclone_pipeline_definitions_util.py` — the source pipeline, route-per-run
  like this one (see [Rclone Source Pipeline](#rclone-source-pipeline-stage-1-configured-per-database))
- `structured_pipeline_definitions(...)` in `util/structured_pipeline_definitions_util.py` — the dlt source pipeline for
  API records, route-per-run (see
  [Structured Source Pipeline](#structured-source-pipeline-stage-1-configured-per-database))
- `default_sharepoint_to_datalake_definitions(...)` / `default_local_filesystem_to_datalake_definitions(...)` in
  `util/definitions_util.py` — deploy-time builders bound to one bucket (SharePoint via MS Graph, local FS)

## Making a Custom Pipeline Selectable in the UI

A deployment can ship its own ingestion pipeline, have it appear in the create-database dialog alongside the platform's,
and give its databases settings of its own, without forking anything. This is the ingestor counterpart of agent-class
discovery.

**Why a database and not a registry.** The API and the pipelines are separate containers. A registry inside a pipeline
can never be read by the API, and one inside the API would list what happens to be installed in the *API* image, which
is the wrong authority: whether an ingestor exists is decided by what is *deployed*. Mongo is infrastructure both sides
already share, so the pipeline writes its own metadata there and the API reads it.

**Why not NATS discovery, the way agents do it.** Agent discovery is a broadcast with a short reply window, which tells
the API that a class is alive right now. It needs that because it dispatches a chat request to an agent synchronously.
Nothing dispatches to a pipeline synchronously, a code location has no always-on subscriber to answer a broadcast (only
sensor ticks measured in tens of seconds), and agent discovery caches into Mongo anyway. The cost of this choice is that
an ingestor never expires: a decommissioned pipeline keeps being offered until its row is deleted. See ADR
`2026_09_04_ingestors_announce_their_configuration_form`.

**What you write.** The labels, and optionally a config class of your own:

```python
defs = document_ingestion_pipeline_definitions(
    ingestor="acme_ocr",  # your routing id, globally unique
    display_name=LocaleString(en="ACME OCR", de="ACME OCR"),
    description=LocaleString(en="OCR-heavy ingestion for scanned contracts"),
    config=AcmeConfig.as_form(llm_model=..., embedding_model=...),  # optional; DocumentIngestionConfig otherwise
)
```

**What is announced.** `Ingestor.from_config()` turns one form-mode config into the two surfaces the API needs: the
elements to render and the JSON schema to validate against. Both come from the same object, so they cannot disagree.
`IngestorConfig` in core is the base and owns the identity fields `name` and `description`, exactly as `AgentConfig`
owns an agent's. `ingestors/document_ingestion_config.py` is the shipped subclass; extend it to add a setting and
nothing in the API or the UI changes.

**What happens then.** The definitions factory adds an `IngestorRegistrationSensorFor_{ingestor}` sensor that ships
`DefaultSensorStatus.RUNNING`, so it is live the moment the code location loads and nobody has to enable it in the
Dagster UI. Every 300 s it upserts an `IngestorEntity` and returns a `SkipReason`; it never launches a run. The upsert
is idempotent and last-writer-wins, so redeploying with a changed label or form updates the row. Form elements are
stored without their `$`-aliases and the schema as a JSON string, the same way `AgentClassEntity` works around Mongo's
key restrictions.

Registration is a **sensor rather than an import-time write** on purpose. A momentary Mongo outage would otherwise take
the whole code location down at load; this way it re-registers on the next tick once the database is back.

**What the API does with it.** `GET /knowledge/ingestors` returns every announced row with labels and form localized.
`create_database` looks the ingestor up, builds a validator from its announced schema, rejects a mismatch with a 400
naming the offending field, walks the announced elements for authorization, and checks every announced model picker
against LiteLLM (mode, tenant access, and a declared `output_vector_size` for embedding pickers). A field the form never
announced is refused the same way, so a mistyped knob cannot be stored and then silently ignored per run. The identity
fields land on the bucket row and everything the form announced in `BucketEntity.configuration`, dumped from the
validated configuration so each knob is stored in the type its pipeline declared. The `ingestor` field is a plain `str`
across the API boundary, not the `IngestorType` enum, so a deployment-defined value is representable on the wire.

**The shipped pipeline is not special.** `document_ingestion` registers through the same sensor, with labels from
`lib.ingestors.document_ingestion.*`. The API has no built-in ingestor and offers nothing until a pipeline is running. A
row that carries labels but no schema (an older pipeline image) is skipped rather than offered.

**Id rules.** `^[a-z][a-z0-9_]*$`, and not a reserved id. `IngestorEntity.reserved_ids()` covers the inert and frozen
routing tokens (`unassigned`, `default_rag`, `shared_rag`, reserved after their code is gone so nothing can adopt a
legacy corpus) plus `datalake`, which would collide with the legacy per-instance streams in the subject grammar.

**The id is not just a label.** Every deployment-global name derives from it, because asset keys are unique per Dagster
deployment and `DynamicPartitionsDefinition` names are global to the instance:

| Derived name             | Shape                                                                                                    |
| ------------------------ | -------------------------------------------------------------------------------------------------------- |
| Asset keys               | `[{ingestor}_datalake_to_vectorstore, data_lake\|documents\|nodes\|…]`                                   |
| Partition registry       | `{ingestor}_document_partitions`                                                                         |
| Job names                | `{ingestor}_source_observation`, `…_remove_documents`, `…_knowledge_teardown`, `…_repair_orphaned_nodes` |
| JetStream stream/subject | `pipeline_{ingestor}_stream` / `pipeline.{ingestor}.>`                                                   |
| Dagster intermediates    | `s3://dagster/{ingestor}/`                                                                               |

That is what lets two pipeline *types* run side by side. It also means **changing the id later strands everything**:
existing databases still carry the old value and stop being claimed, and the old stream, partitions and asset history
are orphaned. Choose it once.

**Failure modes, all at `Definitions`-build time (loud, not silent):**

| Situation                                  | Result                                                  |
| ------------------------------------------ | ------------------------------------------------------- |
| Custom id, no `display_name`/`description` | `ValueError`, it could only render as a bare id         |
| Reserved id (`datalake`, `default_rag`, …) | `ValueError`, it would collide or adopt a legacy corpus |

If the pipeline never appears in the dialog, check in this order: the code location loaded, the sensor exists and is
running in the Dagster UI, the `ingestors` collection has your row with a `config_specs` field, and the API can reach
the same Mongo.

## Rclone Source Pipeline (Stage 1, configured per database)

A knowledge database has two independent axes: its `ingestor` (how files are processed, Stage 2) and its `source` (where
files come from, Stage 1). `BucketEntity.source` + `source_configuration` sit next to `ingestor` + `configuration`;
`source = None` means manual upload, there is no "unassigned" token. A source pipeline announces itself, is configured
and is resolved per run exactly like an ingestion pipeline. See ADR
`2026_09_09_source_pipelines_as_a_second_axis_of_a_knowledge_database`.

**What you write.** `app/rclone_pipeline/__init__.py` is the whole deployed app:

```python
defs = rclone_pipeline_definitions(
    source="rclone",  # routing key; namespaces every global Dagster name (default)
    display_name=LocaleString(en="…"),  # required for a custom source, defaulted for `rclone`
    description=LocaleString(en="…"),
    config=None,  # announced form; defaults to RcloneSyncConfig.as_form()
    settings=RclonePipelineSettings(),  # RCLONE_PIPELINE_OBSERVE_JOB_HOUR/MINUTE, MAX_PARTITIONS
)
```

The asset graph carries **no bucket, remote or credential**. There are no `RCLONE_<SOURCE>_*` env vars and no deployment
defaults for a source: a database without a valid source configuration must not sync.

**Registration record.** A `SourcePipelineRegistrationSensorFor_{source}` sensor upserts a `SourcePipelineEntity`
(collection `source_pipelines`, mirrors `IngestorEntity`: labels, form elements, `config_specs`) every 300 s.
`GET /knowledge/source-pipelines` serves the announced rows; the create-database dialog renders the source form as a
second section of the same dialog; `PUT /knowledge/databases/{database}/source` replaces a database's source and its
configuration (credentials rotate, so unlike the ingestor configuration this one is replaceable) and takes effect on the
next run. The API validates a submission through the same chain as the ingestor form.

**Announced form.** `source_pipelines/rclone_sync_config.py` — `RcloneSyncConfig(SourcePipelineConfig)`: `backend_type`
(`onedrive | drive | s3 | azureblob | sftp | local`), `root_path`, `include_patterns`, `exclude_patterns` and one nested
`Form` per backend whose fields are shown only for the selected backend (`condition_if` on `rclone_backend_type`).
Option groups are non-nullable with primitive defaults, so a hidden group submits nothing and validates as its defaults.
SharePoint is `onedrive` with `drive_type=documentLibrary`. Credentials are `str | Password`;
`SourcePipelineConfig.secret_field_paths()` derives their dotted paths from the form, the API encrypts them with
`SecretEncryptionService` (`AIHUB_CONFIG_ENCRYPTION_KEY`, shared with the pipeline) and returns a mask; a resubmitted
mask keeps the stored value. The dialog offers only `RcloneSyncConfig.offered_backends()` (`_TESTED_BACKENDS` = `s3`,
`drive`, `onedrive`, plus `local` when `RCLONE_LOCAL_SOURCE_ROOT` is set), each under a translated label; the other
backends stay in the form and runtime so existing databases keep syncing. rclone's setup still asks questions in
non-interactive mode: `RcloneClient` answers the fixed ones (`_ANSWERED_QUESTIONS`), OneDrive's drive lookup is answered
with the stored `drive_id` through ephemeral `config_*` parameters (rclone then checks the drive against Microsoft Graph
while creating the remote), and a step rclone fails raises its `Error` text. The Drive service-account key is a
`SecretFileInput` (core form element, treated as a secret by `SecretFieldWalker`). Adding a backend = one `Form`
subclass + one field on `RcloneSyncConfig` + labels in
`packages/core/swiss_ai_hub/core/i18n/translations/lib/source_pipelines.*.yml`. Nothing in the API or UI changes.

**Per-run resolution** (`util/source_builders.py`, the Stage-1 sibling of `model_builders` / `store_builders`):

- `source_config_for_bucket(bucket, source, RcloneSyncConfig)` — row → decrypt → validate; raises if the database is
  `deleting` or its `source` is a different token.
- `rclone_remote_for_bucket(bucket, source)` — upserts the remote `rclone_{bucket}` in the rclone daemon
  (`config/create` with `obscure`, `nonInteractive`) **once per process** (`@cache`; every Dagster step is its own
  process), so a credential edit applies on the next run and the daemon (`--config=/dev/null`, in-memory) needs no
  operator action after a restart. Returns an `RcloneRemote` (name, `fs`, patterns). Secrets travel only in the
  `config/create` body; URLs, logs and metadata carry the name.
- `build_rclone_client()` — stateless `RcloneClient` (RC URL + basic auth), `@cache`d.

The bucket travels in the `aihub/bucket` run tag on the observe/remove path and in the composite
`{bucket}|{remote path}` partition key on the write path. One `rclone_source_partitions` registry is shared by every
database and reconciled per bucket. `per_bucket_observe_schedule(observe_job, owns=owned_by_source(source), …)` fans out
one bucket-tagged run per owned database daily (`owned_by_ingestor` is the Stage-2 predicate, both in
`util/run_routing.py`).

**Namespaces are generated.** Files land at `s3://{bucket}/{top-level folder}/…` and the ingestion pipeline maps the
first path segment to a namespace. Files directly at the root of `root_path` are skipped and counted in the observation
metadata. A folder whose name sanitises to a namespace another folder already owns (`hr docs` next to `hr_docs`) is
skipped too (`NamespaceCollisionError`, listed in the ingestion observation's metadata); removal compares URIs only
(`list_ingestible_uris`), so renaming that folder at the source repairs the database. A sourced database refuses manual
upload, hand-made namespaces and manual document deletion; it may be deleted as a whole.

**Reaching the ingestion pipeline.** After every written or removed file `util/source_updated_notifier.py` publishes a
`SourceUpdatedEvent` on the owning ingestor's subject through the core `SourceUpdatedPublisher` (the same publisher the
API uses for uploads), so the ingestion pipeline picks the change up within its sensor interval instead of at its next
daily observation. `rclone_remove_source_files` is chained after the observation via `run_after_success_sensor` and
announces each removal the same way.

**Cleanup.** `SourceBucketCleanupSensorFor_{source}` (`sensors/source_bucket_cleanup_sensor.py`) drops the partitions
and the daemon remote of every database that still has partitions but no live row pointing at this source. Storage
teardown stays with the ingestion pipeline.

**A second source pipeline type** registers the same way: a `SourcePipelineConfig` subclass for its form, a factory
shaped like `rclone_pipeline_definitions(source="acme_sync", display_name=..., description=..., config=...)` (or
`announced_source_pipeline_sensor(...)`, the reserved-id and label gate every source pipeline builds through, wired into
hand-built `Definitions`), and its own `source` token. The structured source pipeline is the second one. Every
deployment-global name derives from that token with suffixes distinct from the ingestion pipeline's
(`{source}_source_to_datalake` asset group, `{source}_source_partitions`, `{source}_source_observation` /
`…_remove_source_files` jobs). **Ingestor and source tokens reserve each other**: both kinds of pipeline name their
Dagster jobs after their token and the single-flight guard matches runs by job name across code locations, so
`SourcePipelineEntity.reserved_ids()` covers every `IngestorType` value plus the `PipelineSourceType` subject tokens,
and the factory raises at `Definitions`-build time for a reserved id or a custom id without labels.

## Structured Source Pipeline (Stage 1, configured per database)

Jira issues, Confluence pages and similar API records are not files, so rclone cannot sync them. The structured source
pipeline runs a dlt source per database and writes each record as a markdown file with YAML frontmatter into that
database's data lake. The unchanged ingestion pipeline parses and embeds it, and #1953 turns the frontmatter into
document metadata. See ADR `2026_10_01_structured_sources_synced_with_dlt`.

**What you write.** `app/structured_pipeline/__init__.py` is the whole deployed app:

```python
defs = structured_pipeline_definitions(
    source="structured",  # routing key (default); every global Dagster name derives from it
    display_name=LocaleString(en="…"),  # required for a custom source, defaulted for `structured`
    description=LocaleString(en="…"),
    config=None,  # announced form; defaults to StructuredSyncConfig.as_form()
    settings=StructuredPipelineSettings(),  # STRUCTURED_PIPELINE_OBSERVE_JOB_HOUR/MINUTE
)
```

A pipeline whose config offers no source kind is built but not announced, so the create-database dialog never offers a
source nothing can be configured for. The shipped pipeline offers three kinds, Jira, Confluence and MediaWiki (see
[The Jira adapter](#the-jira-adapter), [The Confluence adapter](#the-confluence-adapter) and
[The MediaWiki adapter](#the-mediawiki-adapter)).

**Adding a source kind** takes:

- an `AbstractStructuredSourceAdapter[TOptions]` subclass with its `kind` and its `display_name` (what the kind dropdown
  shows; the token is what gets stored)
- an options `Form` whose every element carries `condition_if=Adapter.shown_for(kind)`
- one field named after the kind on `StructuredSyncConfig`, and the adapter in its `adapters()`
- labels under `lib.source_pipelines.structured.config.*`

The adapter declares:

- `dlt_source(options)`, incremental: on the record's last update (Jira), or on a fingerprint per record kept in the
  resource state when a record can change place without a new update (Confluence). Credentials arrive as arguments,
  never through dlt's configuration providers, which are shared by the whole process.
- `to_record_file(record)` → `StructuredRecordFile`: the namespace (first folder), the path segments, frontmatter using
  #1953's reserved keys (`title`, `url`, `created`; the record's `updated` is kept as ordinary metadata) and the body.
  It must be a pure function of the record. A record may also be a binary file the source offers: it returns a
  `StructuredFileReference` (path with the file's own extension, download URL, size, title, link) instead, and the
  adapter implements `read_file(options, reference)`, which the destination calls while loading.
- `list_record_paths(options)`: the key of every record in scope, built with `StructuredRecordFile.object_key_for` and
  never through the incremental state. It raises rather than returning a partial set.
- `layout_version`: raise it when `to_record_file` changes where or how records are written.

`playground/structured_demo/demo_records_adapter.py` is the smallest working example, `source_pipelines/jira/` and
`source_pipelines/confluence/` complete ones against real APIs.

**One run per database per day.** `per_bucket_observe_schedule(owns=owned_by_source(source))` launches one run per
database, tagged `aihub/bucket`. The single asset `[{source}_source_to_datalake, records]` chains, inside that run:

1. **sync**: config through `source_config_for_bucket` (decrypted) → restore the state → `DagsterDltResource.run` with
   the adapter's `file_source` into `StructuredDataLakeDestination` → save the state
2. **list**: the adapter's listing. It takes the sync's output as input, so it always runs after the sync.
3. **reconcile**: files to remove = present − listed − written this run
4. **delete** and **announce**: the routed ops the rclone pipeline uses, unchanged

Steps hand their values over per run (`storage/{run_id}/…`). Never split them into assets: an asset's value is stored
under its key, which every database shares.

**Writes.** `StructuredDataLakeDestination` writes a file only when the MD5 of its content differs from the stored
object's ETag, then announces the batch through `notify_source_updated`. dlt delivers at least once, so this is what
keeps a run with no changes from writing or announcing anything. Don't replace it with a hash kept as object metadata:
ingestion copies every metadata key of a file into its document and embeds it with each chunk.

Records become files in the extract step (`add_map` in `file_source`), because dlt coerces ISO timestamps into datetimes
before loading. The mapped rows keep every field of the record, so the cursor and the primary key still resolve.

**Files.** A binary file travels as a reference (`FILE_COLUMN`, JSON of a `StructuredFileReference`), never as content
through dlt. The destination downloads it through `read_file`, one at a time, and writes it on the markdown path:
`DataLakeFile.from_content` and one `put_object`, whose ETag is the content's MD5 at any size, so the comparison above
covers files too. Its only object metadata are `document_title` and `source_origin`, which ingestion reads as the
document's title and citation link. Adapters keep a file's fingerprint (the source's checksum and the key) in their
resource state under `FILES_SEEN`, so an unchanged file is never downloaded. The dlt destination keeps its name
`markdown_data_lake` from before files: dlt stores it in every database's state. See the 2026-10-30 amendment of ADR
`2026_10_01_structured_sources_synced_with_dlt`.

**State.** dlt cannot restore state from a custom destination, so each database's ~1 KB `state.json` is kept at
`s3://{database}/.{source}_dagster/state.json`:

- data-lake listings skip `.…dagster` folders
- the `dagster` bucket would expire it within a day
- teardown deletes it together with the bucket

It is keyed by a scope fingerprint (the non-secret options plus `layout_version`): a changed scope or layout re-reads
everything, while a rotated credential keeps the cursor.

**Rules.** Each one guards a failure that would otherwise be silent.

01. **`restore_from_destination = False`** on every pipeline. Otherwise `DagsterDltResource` drops the restored state,
    and every run re-reads everything.
02. **Save the state only after the whole sync succeeded**, and only if the database still uses this source and isn't
    `deleting`. dlt advances the cursor before it writes.
03. **Deactivate dlt's pipeline after the sync** (`Container()[PipelineContext].deactivate()`). Every step of a run
    shares one process (`in_process_executor`), and a listing must never read the sync's cursor.
04. **List after the sync, never before.** A failing listing raises, and an empty listing while the bucket holds files
    raises.
05. **Never remove a file the same run wrote.**
06. **A record listed without a file in two runs in a row means the cursor is ahead of the data.** The state is
    discarded, and the next run re-reads everything. Missing once is remembered in the state (`missing_keys`), not acted
    on: a record created while a run is between its sync and its listing is missing too, and the next incremental run
    fetches it. Discarding at once made a busy source re-read everything night after night.
07. **One sync per database at a time.** A run that finds another sync of the same database running gives way, whichever
    was created first. "Another sync" is a run of the sync job or one launched from the asset page (`__ASSET_JOB` with
    the asset selected); never match on the bucket tag alone, because the database's ingestion runs carry it too.
08. **dlt telemetry stays off.** `structured_pipeline_definitions` sets `RUNTIME__DLTHUB_TELEMETRY=false`, and so does
    the Dockerfile.
09. **Values passed between steps carry no config or secret** (`StructuredSyncOutcome`, `StructuredListing`), because
    step outputs are pickled into the `dagster` bucket.
10. **A file the source will not serve is skipped, never fatal, and never counted as missing.** `read_file` raises
    `StructuredFileUnavailableError` for it (gone, forbidden, too large); any other error fails the load, which dlt
    retries. The destination names it in `failed_keys`; the state store removes it from every `FILES_SEEN` map before
    saving, so the next run tries it again; and it travels to reconcile as `unread_file_keys`, which rule 6 skips.
    Counted as missing, a file that stays unavailable would discard the state every second run and re-read the whole
    source.

**Try it locally.** `make structured-pipeline` runs the ingestion pipeline and `app.structured_pipeline` (Jira,
Confluence) in one `dagster dev`; `playground/jira_seed` fills a Jira Cloud or Data Center test site with the cases to
check (see its README). `make structured-demo` runs the ingestion pipeline and `playground.structured_demo` (token
`structured_demo`) instead, which needs no external system:

1. With the dev stack, API and web up, create a database with the "Demo records (JSON file)" source.
2. Launch `structured_demo_source_sync` with the tag `aihub/bucket=<database>`.
3. Edit `playground/structured_demo/demo_records.json` to see updates and removals.

The demo registers a `structured_demo` row in your dev Mongo's `source_pipelines`; delete it afterwards.

### The Jira adapter

`source_pipelines/jira/` holds the kind: options form, preflight, issue and comment models, and JQL timestamps.
`resources/jira/` holds the HTTP client and its error. One adapter serves Jira Cloud and Jira Data Center (the
`deployment` option); the differences live in `JiraClient`. Every rule below guards a failure that would otherwise be
silent:

- **Credentials go through `auth=` only** (`HttpBasicAuth` on Cloud, `BearerTokenAuth` on Data Center), never through
  headers, which dlt logs at DEBUG.
- **Every request carries the error hook.** It raises `JiraRequestError`, an `HTTPError` with `.response` set, which is
  what keeps dlt's retry of 429 and 5xx (honouring `Retry-After`). Everything else fails at once, a redirect included:
  requests runs the hook before following one, so no answer can send a request on to a host nobody checked.
- **Only public hosts.** A knowledge administrator sets the URL, and the pipeline sits on the networks of the platform's
  own services. The URL type refuses `?`, `#` and credentials (a `?` would turn the appended API path into a query), and
  `SourceHostGuard` (core `network/`, shared with agents that read Jira) refuses, first thing in the preflight, a host
  without a dot (Docker service names, `localhost`) and one resolving to any non-global address.
  `STRUCTURED_PIPELINE_ALLOWED_PRIVATE_HOSTS` exempts named hosts (`localhost` in `.env.dev`). DNS rebinding between the
  check and the request is not covered.
- **Preflight before the sync and before the listing** (`JiraPreflight`: `/myself`, each project, the JQL clause). Jira
  answers a project the account cannot see, and on Cloud an invalid JQL clause, with zero issues, which the listing
  would take for deleted issues. Cloud's clause is checked with `POST /rest/api/3/jql/parse?validation=strict`; Data
  Center's search answers 400 itself. A renamed project still answers to its old key, so the preflight compares the key
  Jira returns.
- **Paging stops only on an empty page or `isLast`, never on a short page.** Cloud returns fewer issues than asked for
  when many fields are requested, and a partial listing deletes files. Cloud pages `/rest/api/2/search/jql` by
  `nextPageToken`; Data Center pages `/rest/api/2/search` by keyset (`id > N ORDER BY id ASC`), which also avoids the
  10,000-result cap of Data Center 11. A page that repeats an issue fails the search (Cloud's tokens have been reported
  to loop), and so does a Data Center search returning fewer issues than its first page counted. Known limit: Data
  Center's `ORDER BY id` sorts by key (checked on 11.3), so the keyset holds only while key order matches id order. An
  issue moved in from another project keeps its old, lower id under a new, higher number, and that project's sync then
  fails on the count check. Core's agent client pages Data Center by offset instead (see `packages/core/CLAUDE.md`).
- **One query per project**: `project = "X" AND (clause)`, with the user's clause in parentheses. An issue of another
  project in the answer is refused (`_own_key`), so no clause can pull in a project the database was not given.
- **File and listing keys come from Jira's returned key** through `JiraIssue.object_key_for`. The namespace keeps case,
  so a key built any other way could differ from the file's, and every file would be removed.
- **Incremental**: the cursor is `updated_at` with `lag=300`. The JQL lower bound is taken from `start_value` once per
  run, written in the `/myself` time zone (JQL dates are read in the account's zone), floored to the minute, and moved
  an hour earlier on a DST fold. `lag` turns off dlt's boundary deduplication, so judge a run by "Files written", not
  "Rows loaded".
- **Comments**: the embedded ones, or the comment endpoint when the issue has more. Restricted (`visibility`) and
  Service Management internal comments are dropped. Data Center marks an internal comment only with the
  `sd.public.comment` property, which search never returns, so service desk projects always read comments from the
  endpoint with `expand=renderedBody,properties`.
- **Text is Jira's rendered HTML**, the one format both editions share, converted with markdownify by core's `JiraHtml`
  (shared with agents that read Jira). Images are dropped, mentions keep only the name, links are made absolute against
  the site (keeping a Data Center context path), and Data Center's `<tt>` becomes code. Plain `_` and `*` stay
  unescaped, so identifiers are indexed as written. Jira's rendered *dates* ("Today 10:15") are never used.
- **Options validators do not run when the API saves a source.** The URL and the edition therefore use type-level
  constraints (a 400 on save), and cross-field checks run in the adapter (`JiraOptions.problems()`).
  `hide_input_in_errors` keeps pydantic from echoing the decrypted token.

### The Confluence adapter

`source_pipelines/confluence/` holds the kind: options, preflight, page model, and storage format → markdown.
`resources/confluence/` holds the HTTP client, its error and the next-link paginator. One adapter serves Confluence
Cloud and Confluence Data Center over REST v1 (`content/search` with CQL); v2 has no CQL search and does not exist on
Data Center. It keeps the Jira adapter's rules on credentials (`auth=` only), the error hook (`ConfluenceRequestError`,
an `HTTPError`, so 429 and 5xx are retried), type-level URL constraints and `problems()`. In addition:

- **Only public hosts, as for Jira.** The URL type refuses `?`, `#` and credentials, and `SourceHostGuard` runs first in
  the preflight with the same `STRUCTURED_PIPELINE_ALLOWED_PRIVATE_HOSTS` exemptions. A Confluence next to a developer's
  pipeline is reached through the dev default `localhost`; an on-premise Data Center on a private address needs an
  operator to allow its host.
- **No redirect is followed.** Every request sends `allow_redirects=False`, and the hook raises on a 3xx naming its
  target, because the guard checked the configured host only.
- **Next links are joined onto the configured site.** Confluence gives `_links.next` relative to the site (`…/wiki` on
  Cloud), which dlt's `JSONLinkPaginator` would join onto the host, losing `/wiki`. `ConfluenceNextLinkPaginator`
  follows only a path below the site, and refuses one that would change the host or port once appended (`@elsewhere/…`,
  `.elsewhere/…`, `:8443/…`).
- **Preflight before the sync and before the listing** (`ConfluencePreflight`): the guard, `user/current` (an anonymous
  answer means the credentials never arrived, and anonymous access reads public pages only), each space, and each parent
  page, which must lie in a listed space. Confluence answers a search in a space or below a page the account cannot see
  with zero pages, which the listing would take for deleted pages. Spaces and pages are found through CQL search
  (`find_space`: `search?cql=type = space and space = "KEY"`; `find_page`: `content/search?cql=id = N`), because Cloud's
  REST v1 no longer serves `space/{key}` or `content/{id}`; v2 does, but Data Center has no v2. A sync's requests
  therefore need only `search:confluence`, plus `read:confluence-user` for `user/current`.
- **Changes are found by `version|path|labels`, not by a cursor.** Renaming or moving a page changes the path of every
  page below it without changing their versions, and neither a move nor adding or removing a label changes any version.
  Each run lists every page in scope without its body (`expand=ancestors,version,space,metadata.labels`), compares each
  page's `version|object key|sorted labels` with the `seen` map in the resource state, and reads bodies only of the
  pages that differ, 25 IDs per CQL query. A page is recorded only once its body was read, so one that vanished between
  the two queries is compared again next time. The map grows with the spaces, some tens of bytes per page.
- **File and listing keys come from `ConfluencePage.path_of`**: the space key, then the titles of the page's ancestors
  and its own. The sync uses it on a full result and the listing on a summary, so the two cannot drift. A title of dots
  alone is written as `page {id}`, since it cannot be a folder or file name. Two pages mapping to one key (a `/`
  sanitised to `_`, the 120-character cut) are logged by the listing, and one of them is kept.
- **Archived pages are dropped by the adapter** (`status == "current"`) rather than left to CQL, so they are removed
  like deleted ones.
- **Frontmatter uses `page_id` and `page_version`**, because #1953 refuses `id` and `version` as platform keys.
- **Text is the storage format**, the body format both editions share, rewritten by `ConfluenceStorage` before
  markdownify. Code and noformat macros become fenced blocks with their language; macros with a body keep it under their
  title; render-only macros (toc, children, jira, include) are dropped; task lists, layouts and ADF fallbacks are kept;
  page links keep their text; images and attachments are dropped. Tables go through core's `HtmlTableConverter`, which
  wraps them in `<table>` tags: `RawLoader` ingests markdown as written, and the table refiner and
  `MarkdownStructuralNodeParser` recognise a table only by that wrapper. An element replaced by an empty string makes
  markdownify strip the whitespace on both sides, so empty elements are removed instead.

### The MediaWiki adapter

`source_pipelines/mediawiki/` holds the kind: options, preflight, scope, page model and rendered HTML → markdown.
`resources/mediawiki/` holds the action API client, the sign-in and the error. It reads the API (`api.php`), never
crawls the HTML pages: the API gives namespace and category scope, revision ids and a complete listing for deletions,
and `action=parse` returns the page with every template expanded but without the skin's navigation. It keeps the
Confluence adapter's rules on the error hook (`MediaWikiRequestError`, an `HTTPError`, so 429 and 5xx are retried),
type-level URL constraints, `problems()` and the `SourceHostGuard` check with
`STRUCTURED_PIPELINE_ALLOWED_PRIVATE_HOSTS`. In addition:

- **API errors arrive with status 200.** The response hook raises on an `error` object (its `code`, such as
  `readapidenied`, is kept on the exception) and on a non-JSON answer, which is what a single sign-on gateway sends for
  an expired session. `parse` alone turns `nosuchpageid` / `missingtitle` into None: a page deleted between listing and
  read is skipped and compared again next run.
- **Four sign-in methods** (`MediaWikiSignIn`): `bot_password` (`action=login`, which takes bot passwords only),
  `web_form` (fills in `Special:UserLogin`), `oauth`, `anonymous`. `oauth` sends the access token of an owner-only OAuth
  2 consumer (Extension:OAuth) as `Bearer` through `RESTClient`'s `auth=`, on every request and never as a header dlt
  could log; a file download sends it as `auth=` too, but only to the wiki's own host (a separate upload host is another
  party); `MediaWikiOptions.oauth_token()` returns it only while `oauth` is selected, so a leftover token never
  travels with a password sign-in. A refused token answers 401: Wikimedia's gateway with `{"httpCode", "httpReason"}`
  (observed 2026-10-30), a bare wiki with MediaWiki's `error` object; `MediaWikiRequestError.from_response` keeps either
  reason, and the preflight turns 401/403 into what to check. The web form exists for wikis whose sign-in an extension
  handles: on wiki.bbv.ch PluggableAuth answers `clientlogin` with a browser redirect the API cannot follow, so only the
  login page works. It sends back every field the form renders (token, provider button) and fills in whichever of
  `wpName`/`username` and `wpPassword`/`password` it has. Redirects are followed by hand, only on the wiki's host and
  never from https to http, because the guard checked that host alone and the session's cookies must not travel.
- **Credentials go through the bare session, never through `RESTClient`**, which logs a POST's form data at DEBUG. The
  signed-in session is then handed to `RESTClient`; its cookies are added when a request is prepared, after dlt logged
  it.
- **No API version to choose.** `api.php` is versioned with MediaWiki itself and deprecates with response warnings
  before removing anything. Every call the client makes exists since MediaWiki 1.27 (bot passwords, the AuthManager
  login form and `meta=tokens` are the newest), so the preflight reads `siteinfo`'s `generator` and refuses an older or
  unrecognisable wiki by name. Checked on 2026-10-30 against 1.43.11 (wiki.bbv.ch), 1.46.2 (wiki.archlinux.org) and
  1.48.0-wmf.1 (mediawiki.org, en.wikipedia.org): no deprecation warnings.
- **The guard runs before the sign-in**, inside `MediaWikiPreflight.check`, so no credential is sent to an internal
  address. The preflight then refuses a session that still reads anonymously (an anonymous listing shrinks to public
  pages and removes the rest), resolves namespaces by number, local or canonical name or `Main` (negative ones refused),
  and checks that every included **and excluded** category exists: a mistyped excluded category would exclude nothing
  and let in exactly the pages it was meant to keep out. A category exists when it has a page or any member, so an
  excluded category whose last member leaves needs a page of its own.
- **Scope is read as page ids** (`MediaWikiScope`): category members through `list=categorymembers`, so a category a
  template assigns counts, then `generator=allpages` per namespace without redirects, with `prop=info` for `lastrevid`
  and the canonical URL. About six requests list 2,700 pages without `apihighlimits`. With `include_subcategories`,
  `category_member_ids` follows `type=subcat` members, each category once, since category trees can loop.
- **One listing per step** (`MediaWikiScope.pages`, cached on the scope): the `pages` and `files` resources and the
  listing step all work from it. Two titles stored at one path (`A//B` and `A__B` are both `Main/A__B.md`) give it to
  the first one listed; the other is logged and left out of the sync as well as the listing, so the stored page cannot
  flip between them with their edits.
- **`user_agent`** (optional) replaces dlt's `User-Agent` on the client's session for every request, sign-in and
  downloads included. Wikimedia's policy asks for a named client with a contact. One printable line only, so the value
  cannot add headers.
- **Changes are found by `lastrevid|object key`**, kept in the resource state like Confluence's `seen` map: a rename and
  a page entering scope keep their revision. Only changed pages are parsed; `created` comes from the oldest revision
  (one request per changed page), `updated` from their parsed revisions in batches of 50. Known gap: a template edit
  re-renders the pages using it without a new revision, so they are re-read only when next edited (`touched` would catch
  it, but also changes on every cache purge).
- **Collections are named after a namespace's canonical name** (`MediaWikiCollections`, resolved by the preflight):
  English for built-in namespaces (`File`, `Project`), as configured for custom ones, `Main` for the main namespace. The
  local name (`Datei` on a German wiki, the site name for the project namespace) changes with the wiki's language or
  site name, and a change would move every document of that namespace and re-ingest it. Two synced namespaces whose
  collections would be stored under one name (after `NamespaceEntity.sanitize_namespace_name`) are refused: pages of the
  same title would compete for one file. The file namespace's own pages may share the file collection, since a page
  (`File/Report.pdf.md`) and a file (`File/Report.pdf`) never share a key. `layout_version` 2 marks the switch from
  local names.
- **File and listing keys come from `MediaWikiPage.path_of`**: the collection, then the title without its prefix split
  at `/` (subpages). A split giving an empty or dots-only folder keeps the title as one file name; a title of dots alone
  is written as `page {id}`.
- **Frontmatter uses `page_id`, `revision` and `categories`** (visible ones only; hidden maintenance categories are
  dropped).
- **Text is the rendered HTML**, rewritten by `MediaWikiHtml` before markdownify. Parser comments, edit sections, the
  table of contents, navboxes, empty elements, footnote back-links and images are dropped, links made absolute against
  the page without their `title`, red links kept as text, and unset template parameters (`{{{name}}}`) removed. A
  **layout table** (one holding another table, or a single row, as a frame, a message box or columns are) is replaced by
  its cells' content, because as data it would put the whole page in one cell. The remaining data tables are converted
  on their own through core's `HtmlTableConverter`, as Confluence does with its own copy of that code: the two kinds
  share no code, so each can change without the other.
- **Files follow the pages** (`sync_documents` and `sync_images`, off by default). `MediaWikiScope.files` asks
  `generator=images` for the files the in-scope pages show or link to, 50 pages per request, with `imageinfo` (URL,
  size, sha1). It keeps only files of the wiki's own repository (a shared one such as Wikimedia Commons is another
  host's content), not in an excluded category (a file page's own categories count; included categories do not, since
  files are in scope through their pages), of a type switched on (`MediaWikiOptions.file_types()`: with `sync_documents`
  pdf, Office 2007+, text; with `sync_images` the image types MinerU knows, `image_types()`, which is why `tif` and SVG
  are not among them; never doc/ppt/pps, archives) and within `max_file_size_mb` (default 50). An image is also left out
  when a page of the Template namespace shows it itself (`MediaWikiScope._template_images`: a template's logo or icon,
  while an image passed as a template parameter is not on the template's page), or when its width or height is below
  `min_image_pixels` (default 100, 0 keeps all). What is left out is counted in the run's log. A file is stored once at
  `File/{name}.{extension in lower case}` and cites its description page. Changes are found by `sha1|key` in
  `FILES_SEEN`.
- **Downloads** (`MediaWikiClient.download`) use the sync's signed-in session (the adapter keeps the client of
  `dlt_source` for `read_file`), follow no redirect, stop reading at the size limit, and refuse an HTML answer: a single
  sign-on gateway answers an expired session with its login page and status 200, which would be stored as the document.
  A file on another host than the wiki's (Wikimedia's upload host) passes `SourceHostGuard` first. 403, 404 and 410
  become `StructuredFileUnavailableError`; a 401 or a server error fails the run.

## Markdown Frontmatter

A `.md` file's leading YAML block becomes document fields and filterable metadata instead of chunked text (#1953). It is
the contract the [structured source pipeline](#structured-source-pipeline-stage-1-configured-per-database) writes its
records in, and it applies to hand-uploaded markdown too.

**Where.** `ops/document/apply_markdown_frontmatter.py` runs in `documents_factory` right after parsing, so neither
figure descriptions nor the table-refinement LLM see the YAML. It reads `.md` URIs only: converters emit markdown too,
and a converted file opening with a horizontal rule must not be taken for YAML. `MarkdownFrontmatter.from_markdown()`
(`types/markdown_frontmatter.py`) parses; `RefDocDocument.with_frontmatter()` returns the applied copy.

| Outcome          | Behaviour                                                                                     |
| ---------------- | --------------------------------------------------------------------------------------------- |
| No leading block | Document passed through untouched (an unclosed `---` counts as no block)                      |
| Not a YAML map   | `MalformedFrontmatterError` → one warning, file ingested exactly as written, block included   |
| Block parsed     | Text becomes the body; one warning per skipped key; op metadata lists stored and skipped keys |

**Contract** (what a writer must produce):

- `title` → `DOCUMENT_TITLE`, `url` → `SOURCE_ORIGIN` (http/https only, it becomes a citation href), `created` →
  `CREATED_AT`. `title` is capped at 500 and `url` at 2,048 characters: both sit on every chunk, twice, and the title is
  embedded with each, so an unbounded one could fail the whole document. `created` is ISO 8601 only, naive = UTC; bare
  numbers are refused (seconds vs milliseconds). **Writers should always emit ISO 8601 with an offset.** A field the
  block omits keeps the data lake value.
- `updated` is **not** reserved: `UPDATED_AT` is when the platform last wrote the document. Uploads bump it
  (`RefDoc.get_or_create_placeholder`), and the knowledge list relies on that to tell a re-upload from a document still
  being deleted. The record's own `updated` is stored as an ordinary key.
- Every other key lands on the document and, through the chunker, on every node and summary node. Names are normalised
  (`normalize_key`: NFKD, ASCII, lowercase, runs of other characters → `_`, edge `_` trimmed, must start with a letter),
  because Milvus filter expressions and Mongo field names accept only plain identifiers and an admin must be able to
  predict the name. First key wins on a collision.
- Values: text, int64, finite floats; `true`/`false`, dates and list items are stored as **text**. llama-index's
  `MetadataFilter` rejects booleans, so a flag must be stored the way a filter can name it. Null, maps and nested lists
  are skipped.
- `MarkdownFrontmatter.PLATFORM_KEYS` (all of `DEFAULT_METADATA` plus llama-index/Milvus internals) are refused, so a
  Jira `type: Bug` cannot replace the content/summary `type` every retrieval filters on. Adapters write `issue_type`.
- `MAX_METADATA_BYTES` (8 KiB, file order) caps the custom metadata: each node stores its metadata twice in Milvus' 64
  KiB dynamic field (keys + `_node_content`).

**Not embedded, but shown to the model.** Custom keys go into `excluded_embed_metadata_keys`: on a short record they
would outweigh the body in its vector. The title stays embedded. The exclusion has to survive every step that rebuilds a
document or node — `refine_document_tables` passes it on, `build_nodes_from_splits` copies it to chunks,
`RecursiveSummaryParser._create_summary_node` (core) copies it to summaries, and the doc store round-trips it. That list
is also how retrieval tells them apart from the platform's own metadata: core's `IngestedNode.from_llama_index_node`
moves exactly those keys into `record_fields`, and `combine_nodes_in_order` writes them into each document's
`<REFERENCE_DOCUMENT>` header, so an agent can answer "what is the status of ENG-2?" (aihub-core-private#362).

**Filtering.** A retriever filters on keys listed in `allowed_metadata_filter_fields`, with values from
`RAGStartEvent.additional_filters`. `MetadataFilterPair.to_llama_index()` (core) turns a text value into
`key == v or array_contains(key, v)`, so one filter matches a scalar and a list without the publisher knowing the shape;
numbers keep plain equality, booleans are compared as `"true"`/`"false"`. Covered against a real Milvus by
`core/.../retrieval/tests/integration/test_retrieve_nodes_metadata_filters.py`.

**Citations.** The OpenWebUI pipe (`GroundingNodesEventHandler.document_link`) links a citation to `reference_url`, else
`source_origin`, and only to http(s). That also gives SharePoint (MS Graph) documents their web link, while the
`remote:path` origins rclone records and local file paths are not links and stay unlinked.

**Not retroactive.** Applying the op changes no data version upstream, so markdown ingested before it keeps its
frontmatter chunks until the file changes or is re-uploaded.

## Per-Database Configuration

Stage 2 serves many knowledge databases, so nothing about how a document is processed can be fixed at build time, any
more than a store can. `util/model_builders.py` resolves it from the bucket, per run, and is the one place to look:

- `ingestor_config_for_bucket(bucket, config_type=DocumentIngestionConfig)` merges what the database stored over the
  deployment defaults (`DocumentIngestionPipelineSettings`) and returns the typed config. A key the row does not carry,
  which is every key added after that database was created, falls back to the default, so old databases keep ingesting
  unchanged. A custom pipeline passes its own subclass to read its extra settings typed.
- `llm_model_name_for_bucket` / `embedding_model_name_for_bucket` / `vision_model_name_for_bucket` read the model slots
  of that config. The vision model falls back to the text model, deliberately: the platform has no dedicated vision
  model, and gemma reads images. A deployment that points the text model at a provider without image input must set
  `DOCUMENT_INGESTION_VISION_MODEL` too — nothing checks this, because LiteLLM's `supports_vision` is undeclared for
  gemma and `true` for the OCR-only MinerU model, so it cannot tell a suitable model apart.
- `embedding_dimension_for_bucket` derives the collection's vector width from the embedding model's declared
  `output_vector_size`, **not** from a `MILVUS_DIMENSION` setting. A dimension configured independently of the model is
  not rejected by Milvus, it silently truncates or pads every vector. The API refuses an embedding model that declares
  no width for the same reason.
- `build_embedding_model` / `build_language_model` / `build_vision_model` are `@cache`d per bucket, so a
  partition-per-document graph reuses one client.
- The enrichment ops read their switch from the same config and pass the document through, or return no nodes, when the
  database opted out. The graph never changes shape per database.

`BucketEntity.carry_over_retired_model_columns()` moves the columns that predate this design into the configuration
object. Both the API (at start) and the registration sensor (every tick) run it, so whichever side is upgraded first
reconciles the rows before a run could read a database whose models had moved.

The configuration is set at create time and is not updatable; `update_bucket` exposes no parameter for it.

**Known gap:** retrieval still reads a per-agent `embed_model`, so a database ingested with one embedding model can be
queried with another. The contract is enforced on the write path only. See ADR
`2026_08_31_per_database_models_and_embedding_contract` and #1820.

## Asset Factory Pattern

All factories return `graph_asset` (multi-op composition). They compose `@op` steps into a single asset:

```python
def my_factory(key: AssetKey, upstream_key: str | AssetKey, partitions: DynamicPartitionsDefinition) -> graph_asset:
    @graph_asset(
        key=key,
        partitions_def=partitions,
        ins={"upstream": AssetIn(key=upstream_key)},
        automation_condition=AutomationCondition.eager(),
    )
    def my_asset(upstream: InputType) -> Output[OutputType]:
        result = op1(upstream)
        return op2(result)

    return my_asset
```

Key factories (all in `assets/factories/`):

- **Stage 1**: `observable_*_factory` (source monitoring), `data_lake_file_factory` (source → DataLakeFile),
  `removed_data_lake_files_factory` (cleanup), `placeholder_refdocs_factory` (placeholder documents);
  `routed_data_lake_file_factory` / `routed_removed_data_lake_files_factory` are the source-pipeline variants that
  resolve the bucket per run and announce each write/removal to the ingestion pipeline
- **Stage 2**: `observable_data_lake_factory`, `documents_factory`, `nodes_factory`, `summary_nodes_factory`,
  `removed_documents_factory`

## Domain Types

| Type                  | Base                  | Key Fields                                             | Storage                         |
| --------------------- | --------------------- | ------------------------------------------------------ | ------------------------------- |
| `DataLakeFile`        | `BaseModel`           | name, namespace, uri, hash, content, filetype          | S3 via DataLakeIOManager        |
| `RefDocDocument`      | LlamaIndex `Document` | namespace, hash, uri, updated (computed from metadata) | MongoDB via DocStoreIOManager   |
| `TextNode`            | LlamaIndex `TextNode` | Used directly — not subclassed                         | Milvus via VectorStoreIOManager |
| `SourceFile`          | `BaseModel`           | name, path, size, modified, content                    | In-memory (not persisted)       |
| `MarkdownFrontmatter` | `BaseModel`           | body, title, url, created, metadata, skipped           | In-memory (applied to RefDoc)   |
| `SharePointFile`      | `SourceFile`          | + download_url, full_url                               | via SharePointIOManager         |
| `RcloneFile`          | `SourceFile`          | + remote, remote_path, hashes, mime_type               | via RoutedRcloneIOManager       |

`DataLakeFile.from_content(uri, content, metadata)` — factory method for creating from raw bytes. `id_` is computed as
`uri_to_id(uri)` (MD5 hash). `RefDocDocument.add_metadata_from_data_lake_file()` enriches documents with standard
metadata keys (`NAMESPACE`, `HASH`, `SOURCE`, `CREATED_AT`, `UPDATED_AT`, `DOCUMENT_TITLE`, etc.).

## I/O Managers

All extend `ConfigurableIOManager` with `handle_output()` and `load_input()`. Support partitioned and non-partitioned
assets.

**Read/Write** (data lake and downstream storage):

- `S3DataLakeIOManager` — S3/MinIO/SeaweedFS. Metadata stored as S3 object tags.
- `AzureDataLakeIOManager` — Azure Data Lake Storage. URL-quoted metadata encoding.
- `DocStoreIOManager` — MongoDB via LlamaIndex `KVDocumentStore`. URI → document ID via `uri_to_id()`.
- `VectorStoreIOManager` — Milvus, **collection resolved per run**. Upsert mode. 30s retry logic for eventual
  consistency. Filters by `DOCUMENT_ID`. After a successful write it also flips the source `RefDoc`'s `is_ingested` to
  `True` (`io/ingestion_marking.py`, resolving each document from `node.ref_doc_id`). This deliberately lives in the IO
  manager, not in an op: the Milvus write happens during output handling, so an op could only ever mark the documents
  *before* their nodes are actually retrievable — which is the bug it guards against. It takes no store name: the bucket
  comes from the composite partition key, and the collection and its vector width from that bucket.
- `RoutedS3DataLakeIOManager`, `RoutedDocStoreIOManager` — the Stage-2 read/write pair, same routing rule.

**Read-Only** (source connectors — `handle_output()` raises `NotImplementedError`):

- `SharePointIOManager` — MS Graph API. Returns `SharePointFile` (partitioned) or `list[MinimalSharePointFile]`.
- `RoutedRcloneIOManager` — Rclone RC API, **remote resolved per run**. On the partitioned read the bucket comes from
  the composite `{bucket}|{remote path}` key and the file is downloaded from that database's remote (`RcloneFile`); on
  the non-partitioned read (removal) the bucket comes from the `aihub/bucket` run tag and only metadata is listed,
  filtered to the keys that database currently has (`list[MinimalRcloneFile]`).
- `LocalFileSystemIOManager` — Pattern-based FS scanner. Returns `SourceFile` or `list[MinimalSourceFile]`.

## Resources

**Data lake hierarchy** (cloud-agnostic abstraction):

- `AbstractDataLakeClient` → `S3DataLakeClient`, `AzureDataLakeClient` (list, get, delete file operations)
  - **Observation cost is per directory, not per object.** `get_all_files()` answers only "which files exist and has any
    changed", which `list_objects_v2` already covers — so it issues no per-object `head_object`, and resolves
    `get_or_create_namespace_for_directory` once per directory rather than per file. The lookup also *registers* the
    `NamespaceEntity` the knowledge UI and namespace-selection agent read, so the first file of each directory still
    reaches it. The download path (`create_data_lake_file_from_uri`, `create_data_lake_files_from_uris`) keeps the head
    because it needs the object's user metadata and content type — it just no longer fetches it twice. `list_objects_v2`
    and `head_object` return the same ETag and modification time, so the `DataVersion` is identical either way; that
    equivalence is pinned by tests, because a divergence would re-parse and re-embed the whole corpus.
- `AbstractDataLakeClientResource` → typed `ConfigurableResource` wrappers for Dagster DI
- `AbstractDataLakeFileSystemResource` → `s3fs`/`adlfs` wrappers for streaming reads

**Source connectors**:

- `SharePointResource` — MS Graph API. Config: `target_folders`, `exclude_folders`, `supported_filetypes`.
- `LocalFileSystemResource` — Pattern-based directory scanner. Config: `base_path`, include/exclude patterns (regex).
- Rclone has **no resource**: the remote, patterns and credentials differ per database, so the source pipeline resolves
  them per run through `util/source_builders.py` and talks to the daemon through a stateless `RcloneClient`
  (`resources/rclone/rclone_client.py`, RC API). Same reason Stage 2 builds its stores instead of injecting them.

**Document processing**:

- `DocumentParserResource` — Selects parser by filetype. `LoaderType.MINERU` (default) or `DOCUMENT_INTELLIGENCE`.
  Fallbacks: `EpubReader`, `IPYNBReader`, `RawLoader`, `RTFReader`, `ImageLoader`.
- `MarkdownStructuralNodeParserResource` — LlamaIndex MD structural parser for chunking.
- `RecursiveSummaryParserResource` — Hierarchical summary generation for multi-level RAG. Takes the database's LLM and
  its `LLMConfig` per call and caps each prompt to that model's input limit, map-reducing over oversized rollups instead
  of sending them whole.
- `TableRefinementResource` — LLM-powered table detection and structure splitting; the model arrives per call.

**LLM/Embedding**: `EmbeddingModelResource` (wraps `EmbeddingModelConfig`), `LanguageModelResource` (wraps `LLMConfig`).
Both use LiteLLM model names and bind one model at build time, so — like the store resources — they serve **Stage 1
only**. Stage 2 resolves its models per database (see [Per-Database Configuration](#per-database-configuration)).

**Storage**: `MongoDocumentStoreResource` (LlamaIndex `MongoDocumentStore`), `MilvusVectorStoreResource` (uri,
collection_name, dimensions, index_type: HNSW or IVF_FLAT). These bind one store at `Definitions`-build time, so they
serve **Stage 1 only**.

**Stage 2 builds its stores instead of injecting them.** A configurable pipeline serves many knowledge databases, and a
Dagster resource is built once per run from an `InitResourceContext` that carries neither the partition key nor (for
auto-materialized runs) a run tag — so a resource cannot know which database it is for. Every bucket-scoped store
therefore comes from `util/store_builders.py`, keyed by a bucket each op and IO manager resolves from its own context
via `util/run_routing.py`. One factory, one `context → bucket → store` shape, no per-run store resources. Do not
reintroduce one: it would recreate the second construction path this replaced.

**Resource factory** (`resources/factory.py`) — assembles resource dicts for `Definitions`. All of these bind one store
at build time, so they serve **Stage 1**; Stage 2 builds its stores per run instead (see below):

- `s3_data_lake_resources(container_name)` — client, file_system, io_manager, resource
- `azure_data_lake_resources(...)` — the Azure equivalent
- `mongo_document_store_resource(store_name)` — doc_store, io_manager, resource
- `default_llm_resources()` — `embedding_model` + `language_model` for pipelines that want fixed models
- `default_io_manager_s3_datalake_resources(container_name)` — Dagster PickleIOManager for inter-op data; intermediates
  land in the shared `dagster` bucket under `<container_name>/` with a bucket-wide 1-day TTL.

## Observable Assets & Dynamic Partitions

Observable assets monitor external sources. Return `DataVersionsByPartition` to signal which partitions changed:

```python
@observable_source_asset(key=key, partitions_def=partitions, io_manager_key="source_io_manager")
def observe_source(context, client: ResourceParam[SourceResource]) -> DataVersionsByPartition:
    files = client.fetch_minimal_files()
    return data_version_by_partition(context, files, partitions, max_partitions)
```

**DataVersion format**: `"{updated}-{hash}"` — detects both timestamp and content changes. The rclone source pipeline
uses `hash:{md5|sha1|first}` when the backend reports hashes, else `mtime:{modified}-{size}`.

**Dynamic partitions**: Partition key = composite `{bucket}|{file URI}` (Stage 2) or `{bucket}|{remote path}` (rclone
source pipeline); the deploy-time Stage-1 builders use the plain file path. Managed via
`replace_partition_keys(context, partition_name, keys, max_partitions)` in `util/partition_utils.py`. Default max: 1000
partitions added/deleted per tick.

**Partition definition naming convention**: `DynamicPartitionsDefinition` names are global within a single Dagster
instance — two factories using the same name will collide and share partition state. The route-per-run pipelines
therefore keep **one registry per pipeline token** (`{ingestor}_document_partitions`, `{source}_source_partitions`) and
reconcile it **per bucket**: the bucket is part of every key, and an observation replaces only the keys with its own
`{bucket}|` prefix. Two databases synced from the same or different sources never share partitions by naming convention
(the #1236 class). The deploy-time builders derive their name from the data lake container and the source instead. Never
hard-code a partition definition name in a factory.

## Automation & Triggering

Four triggering mechanisms work together:

- **Eager automation**: `AutomationCondition.eager()` on downstream assets — materialize immediately when upstream
  changes. Enabled by `default_automation_sensor(assets, minimum_interval_seconds=60)`.
- **NATS sensor**: `nats_document_uploaded_sensor` — polls JetStream for `SourceUpdatedEvent` via
  `PipelineTypeTopicManager`. Triggers the observe job when documents are uploaded externally (e.g., via API). **One
  stream per pipeline, not per database**: the subject is keyed on the ingestor
  (`pipeline.{ingestor}.{bucket}.to.knowledge.{db}.…`), so the sensor holds a single stream and a single durable
  consumer however many databases it serves. Each tick drains that stream once, groups the batch by the bucket in the
  subject, and then decides per database. **Single-flight**: an observation scans the whole bucket, so the sensor never
  requests a second one for that bucket while one is queued or running (`SingleFlightRunGuard`, filtered by the
  `aihub/bucket` tag — without that filter one database's run would suppress every other's). It does not cancel or queue
  runs; the second request is simply never made. Events seen during a run arm exactly one follow-up via that bucket's
  cursor (`PerBucketObservationSensorCursor` wrapping `ObservationSensorCursor`), because a running observation may
  already have listed the bucket before those files landed. A 30 s debounce (`DEBOUNCE_SECONDS`) collects a burst into
  one request, and the whole JetStream backlog drains per tick rather than one fetch of ten. Run keys are derived from
  the highest stream sequence plus a re-arm counter, so Dagster's own run-key deduplication acts as a second line of
  defence.
- **Teardown sensor**: `knowledge_teardown_sensor` — no NATS at all. It enumerates the `BucketEntity` /
  `NamespaceEntity` rows flagged `deleting` and requests a teardown run per flagged row. The flag *is* the durable
  request, so nothing can be acknowledged and then lost. The run key is numbered by how many runs the target has already
  had, which keeps it stable while an attempt is pending and lets a failed teardown re-drive.
- **Daily schedules**: `daily_schedule_at(job, hour, minute)` — cron-based observation for sources that don't push
  events.
- **Run-status chaining**: `run_after_success_sensor(monitored_job=..., triggered_job=...)` — fires `triggered_job`
  after `monitored_job` succeeds. Used to order observe → remove jobs, since Dagster forbids mixing observable source
  assets with regular assets in a single `define_asset_job` selection. All definition builders wire this automatically;
  the remove job no longer has its own schedule. Single-flight applies here too: the removal also compares the whole
  corpus, so one already in flight covers the observation that just succeeded, and the request is keyed on the observing
  run id so retries deduplicate. With `require_bucket_tag=True` the triggered run inherits the observe run's
  `aihub/bucket` tag and the coverage check is scoped to that bucket.

**Run priority**: `observe_source_job` and `materialize_asset_job` tag their runs `dagster/priority: "10"`
(`ORCHESTRATION_RUN_PRIORITY` in `jobs/factory.py`). `QueuedRunCoordinator` sorts the whole queue by that tag before
trimming to the dequeue batch, but every run defaults to `0` — which collapses the sort into plain FIFO and lets a bulk
upload strand an observation behind the hundreds of per-document ingestion runs it just authorized. Observation and
removal are cheap and gate everything downstream, so they jump the backlog. This is ordering only, not reserved
capacity: no slot is ever held idle, and ingestion still uses every slot when nothing else is waiting. Dagster cannot
preempt a *running* run, so the wait is bounded by one ingestion run rather than by zero. Only the sensor daemon and the
scheduler apply a job's `run_tags`, so runs launched through `DagsterGraphQLClient` (or any caller that passes its own
tags) land at priority 0 — the sensor, chaining sensor and daily schedule paths, which is every automated launch, all
carry it.

**Partition-set convergence**: `replace_partition_keys` caps additions and deletions at `max_partitions` (default 1000).
When it truncates, it logs a warning and tags its own run with `PARTITIONS_TRUNCATED_TAG` — a run cannot write its
sensor's cursor, so the fact that the partition set has not converged travels back as a run tag. The NATS sensor re-arms
on an unhandled truncation tag and records the run id it answered, chaining observations until one truncates nothing.
Without this, single-flight would trade the run storm for partially observed batches above 1000 files.

## Repairing Orphaned Vector Nodes

`{ingestor}_repair_orphaned_nodes` (`jobs/repair_orphaned_nodes_job.py` → `ops/repair/repair_orphaned_nodes_op.py` →
`services/orphaned_node_repair_service.py`) deletes the Milvus nodes of documents that have neither a doc store record
nor a file in the data lake. It is never scheduled: it scans every partition the database's namespaces hash to, plus
`_default`, which is too expensive to run after each removal. Launch it by hand from the Launchpad with the
`aihub/bucket` run tag. It is a **dry run by default**; set
`ops: {repair_orphaned_nodes_op: {config: {dry_run: false}}}` to delete. The step's output metadata lists orphaned
documents, orphaned nodes, deleted nodes and a per-document table.

Safety: the keep set includes data-lake files, so a document between landing and record creation is kept; each delete
batch re-checks that no record was created since the scan; nodes are deleted by the scanned primary keys, so nodes
written after the scan (fresh uuids) are never touched.

## Run-Failure Notifications

A separate sensor fires on every **failed run** in the code location and dispatches via Apprise to any configured
channel (80+ services: Slack, Teams, Discord, Telegram, PagerDuty, mailto, webhook, …). One sensor covers both job-based
runs (observe/materialize/remove) and the runs spawned by the auto-materialize sensor — so asset-centric pipelines get
failure alerts without per-asset wiring.

- **Factory**: `run_failure_notification_sensor(urls=..., dagster_ui_base_url=..., monitored_jobs=..., ...)` in
  `swiss_ai_hub.pipeline.sensors.run_failure_notification_sensor`. Wraps
  `dagster_apprise.AppriseResource.notify_run_status` with a custom message body (asset keys, error preview, deep link
  to the Dagster UI).
- **Opt-in via env**: set `NOTIFICATION_URLS` (comma-separated Apprise URIs) to enable; leave empty to disable.
  `NotificationSettings` reads `NOTIFICATION_URLS`, `NOTIFICATION_DAGSTER_UI_BASE_URL`, `NOTIFICATION_TITLE_PREFIX`,
  `NOTIFICATION_MIN_INTERVAL_SECONDS`.
- **Automatic wiring**: the Stage-1 builders and `document_ingestion_pipeline_definitions()` append the sensor
  automatically when the env is configured — consumer code in `app/*/__init__.py` needs no change.
- **Manual composition**: consumers that build their own `Definitions` can import the factory directly and narrow
  `monitored_jobs=[...]` to specific jobs.

## Playground

- `playground/__init__.py` — the real `document_ingestion_pipeline_definitions()` pipeline, plus a sensor that registers
  the playground's own knowledge database
- `playground/quick_start/simple_pipeline.py` — Hello-world: 2 basic assets, no external deps
- `playground/quick_start/my_document_pipeline.py` — Complete pipeline with all factories, resources, sensors

Start: `make playground` or `uv run dagster dev -m playground` Access: http://localhost:3000 (Dagster UI)

**Launching an observe, remove or repair run by hand** (from the Dagster UI's Launchpad) requires the `aihub/bucket` run
tag — `aihub/bucket: playground` in the playground. Those runs learn their target database from the tag, not from a
partition key, so without it the run fails with a `ValueError` naming the missing tag. Sensor- and schedule-launched
runs set it for you; only manual launches need it.

## Local Dagster Instance

`make playground`, `make quickstart`, `make document-ingestion-pipeline`, `make structured-pipeline` and
`make structured-demo` each depend on the `dagster-home` target, which installs `dagster.local.yaml` into
`$(DAGSTER_HOME)` as `dagster.yaml` (copy-if-absent), and source the repo-root `.env` for the dev-stack connection
settings. Two failure modes this prevents: an unset `DAGSTER_HOME` makes `dagster dev` create a throwaway
`.tmp_dagster_home_*` instance per start, and a missing instance config leaves `DefaultRunCoordinator` in place, which
fans out runs with no cap and storms MinerU. `dagster.local.yaml` uses the same `QueuedRunCoordinator` as
`infra/configs/dagster/dagster-config.<stage>.yml`, but with `max_concurrent_runs` as a literal instead of
`env: DAGSTER_MAX_CONCURRENT_RUNS`. Keep it literal: the file is installed into `$DAGSTER_HOME`, so an unresolvable env
var would raise `PostProcessingError` in every Dagster process on the machine, including ones started without the repo
`.env` loaded.

`DAGSTER_HOME ?= $(HOME)/.dagster_home` is defined in the Makefile and exported over whatever `.env` says — same
directory, but already absolute, so the recipes can `mkdir`/`cp` with it. `.env` keeps the tilde form for the manual
`set -a && source .env && set +a` flow, where Dagster's own `expanduser` resolves it.

Do NOT use the `-include ../../.env` + `export` pattern from `packages/api/Makefile` here. Make keeps the quotes from
`.env`, so every value arrives wrapped in literal apostrophes — `DAGSTER_HOME='~/.dagster_home'` reaches Dagster with
the quotes attached and is rejected as a non-absolute path. Source the file in the recipe instead.

`dagster.local.yaml` is local-only: Dagster reads no filename but `dagster.yaml`, so the copy in this directory is inert
where it sits, including inside the pipeline images that `COPY packages/pipeline`.

## App Entry Points

`app/` contains deployable Dagster gRPC code locations:

- `document_ingestion_pipeline/` — **the** document ingestion pipeline. One deployment ingests *every* knowledge
  database whose `BucketEntity.ingestor` is `document_ingestion`, resolving the target bucket per run (composite
  partition key `{bucket}|{uri}` on the write path, `aihub/bucket` run tag on the observe/remove path). Built by
  `document_ingestion_pipeline_definitions()` in `util/document_ingestion_definitions_util.py`. Creating a knowledge
  database needs no new code location, compose service, or env var. A deployment's own pipeline can run alongside it and
  be user-selectable — see [Making a Custom Pipeline Selectable](#making-a-custom-pipeline-selectable-in-the-ui) and ADR
  `2026_06_18_rag_pipeline_route_per_run`.
- `rclone_pipeline/` — **the** rclone source pipeline (Stage 1). One deployment syncs *every* knowledge database whose
  `BucketEntity.source` is `rclone`, from the backend and credentials stored on that database. Built by
  `rclone_pipeline_definitions()` in `util/rclone_pipeline_definitions_util.py`. Compose service `rclone_pipeline`
  (built from `app/rclone_pipeline/Dockerfile`, a copy of the ingestion one whose `PIPELINE` default is
  `rclone_pipeline`, because the release workflow builds `app/<name>/Dockerfile` with `VERSION` as its only build arg),
  workspace entry `rclone_pipeline:4000`, env `AIHUB_CONFIG_ENCRYPTION_KEY`, `RCLONE_URL`, `RCLONE_RC_USER/PASS`,
  `RCLONE_PIPELINE_OBSERVE_JOB_HOUR/MINUTE`. See
  [Rclone Source Pipeline](#rclone-source-pipeline-stage-1-configured-per-database).
- `structured_pipeline/` — **the** structured source pipeline (Stage 1). One deployment syncs *every* knowledge database
  whose `BucketEntity.source` is `structured`, from the source kind and credentials stored on that database, via dlt.
  Built by `structured_pipeline_definitions()` in `util/structured_pipeline_definitions_util.py`; Dockerfile as rclone's
  with `PIPELINE=structured_pipeline` and `RUNTIME__DLTHUB_TELEMETRY=false`. Compose service `structured_pipeline`
  (container `structured-pipeline`), workspace entry `structured_pipeline:4000`, env `AIHUB_CONFIG_ENCRYPTION_KEY`,
  `STRUCTURED_PIPELINE_OBSERVE_JOB_HOUR/MINUTE`. Unlike the rclone pipeline, which leaves the internet to its daemon, it
  calls the business application's API itself, so it is the one pipeline on the `egress` network. See
  [Structured Source Pipeline](#structured-source-pipeline-stage-1-configured-per-database).

The legacy `default_rag_pipeline` / `shared_rag_pipeline` are **gone**: their code is deleted and their last published
images are pinned in the `nightly` and `latest` compose stages so existing corpora keep ingesting. They can never be
rebuilt and there is no migration path — see ADR `2026_08_31_legacy_rag_pipelines_frozen_and_removed`. Their bucket
names (`defaultknowledge` / `sharedknowledge`) and routing tokens (`default_rag` / `shared_rag`) stay reserved so
nothing can be created on top of them, and rows predating the `ingestor` field read the inert `unassigned` default.

`document_ingestion_pipeline` has a `Dockerfile` (Python 3.13-slim, uv, port 4000):
`dagster api grpc -h 0.0.0.0 -p 4000 -m "app.document_ingestion_pipeline"`

Run it locally: `make document-ingestion-pipeline`. The rclone source pipeline runs on the host the same way with
`dagster dev -m app.rclone_pipeline` against the dev stack's daemon (`RCLONE_URL=http://localhost:5572`). The structured
source pipeline runs with `make structured-pipeline` (Jira, Confluence, MediaWiki), or `make structured-demo` with the
playground's demo source, each next to the ingestion pipeline as a second code location.

## Testing

- pytest with pytest-asyncio
- Unit test ops: `build_op_context(resources={...})` → call op → assert
- Integration test assets: `materialize(assets=[...], resources={...}, partition_key="test")` → assert `result.success`
- Test markers: `self_hosted`, `slow`, `integration`, `experimental`, `flaky`

## New Pipeline Checklist

1. Choose approach: `document_ingestion_pipeline_definitions()` for Stage 2, `rclone_pipeline_definitions()` for a
   Stage-1 source pipeline. A new external source usually needs **no pipeline at all**: users configure it per database
   in the create dialog; a new rclone backend is a `Form` subclass in `source_pipelines/rclone_sync_config.py` + i18n
   labels
2. For a new source pipeline *type*: a `SourcePipelineConfig` subclass, an observable factory routed by run tag, a
   read-only routed source I/O manager, and per-run resolution in the style of `util/source_builders.py`
3. For custom processing: create ops in `ops/`, compose into `@graph_asset` factory in `assets/factories/`
4. Wire into `Definitions` with resources, sensors, jobs, schedules
5. If it is a **pipeline users should be able to pick**: choose a permanent `ingestor` (Stage 2) or `source` (Stage 1)
   id and pass `display_name`/`description`, and declare any setting of your own on a `DocumentIngestionConfig` /
   `SourcePipelineConfig` subclass passed as `config`. See
   [Making a Custom Pipeline Selectable](#making-a-custom-pipeline-selectable-in-the-ui) and
   [Rclone Source Pipeline](#rclone-source-pipeline-stage-1-configured-per-database). Verify the row lands in the
   `ingestors` / `source_pipelines` collection and the entry appears in the create-database dialog with your form.
6. Test in playground: `make playground` → materialize in Dagster UI at http://localhost:3000
7. Deploy: create `app/{pipeline_name}/` with `__init__.py` + `Dockerfile`, and add a code location to
   `infra/deployment/templates/configs/workspace.yml.j2` plus an image entry in `infra/deployment/compose-config.yml`,
   then `make generate-compose`
8. Run `make test`

## Essential Files

**Core Entry Points**:

- Stage-2 builder: `packages/pipeline/swiss_ai_hub/pipeline/util/document_ingestion_definitions_util.py`
- Stage-1 source pipeline: `packages/pipeline/swiss_ai_hub/pipeline/util/rclone_pipeline_definitions_util.py`
- Stage-1 deploy-time builders: `packages/pipeline/swiss_ai_hub/pipeline/util/definitions_util.py`
- Resource factories: `packages/pipeline/swiss_ai_hub/pipeline/resources/factory.py`

**Asset Factories**:

- Stage 2: `packages/pipeline/swiss_ai_hub/pipeline/assets/factories/data_lake_to_vector_store/`
- Stage 1 generic: `packages/pipeline/swiss_ai_hub/pipeline/assets/factories/source_to_data_lake/`
- SharePoint: `packages/pipeline/swiss_ai_hub/pipeline/assets/factories/share_point_to_data_lake/`
- Rclone: `packages/pipeline/swiss_ai_hub/pipeline/assets/factories/rclone_to_data_lake/`
- Local FS: `packages/pipeline/swiss_ai_hub/pipeline/assets/factories/local_files_system_to_data_lake/`

**I/O Managers**: `packages/pipeline/swiss_ai_hub/pipeline/io/` — S3DataLakeIOManager, AzureDataLakeIOManager,
DocStoreIOManager, VectorStoreIOManager, SharePointIOManager, RoutedRcloneIOManager, LocalFileSystemIOManager

**Domain Types**: `packages/pipeline/swiss_ai_hub/pipeline/types/` — DataLakeFile, RefDocDocument, SourceFile,
SharePointFile, RcloneFile, RcloneRemote

**Resources**: `packages/pipeline/swiss_ai_hub/pipeline/resources/` — data_lake/ (base, s3, azure), parser/,
vector_store/, doc_store/, llm/, share_point/, rclone/ (client only), local_file_system/

**Sensors**: `packages/pipeline/swiss_ai_hub/pipeline/sensors/` — `nats/nats_document_uploaded_sensor.py` (uploads),
`knowledge_teardown_sensor.py` (deletions), `ingestor_registration_sensor.py` / `source_pipeline_registration_sensor.py`
(labels + form announcement), `source_bucket_cleanup_sensor.py` (forget databases that left a source),
`run_after_success_sensor.py` (job chaining), `run_failure_notification_sensor.py` (alerting)

**Route-per-run core** (read these before touching Stage 2 or the source pipeline): `util/run_routing.py` (how a run
learns its bucket, `owned_by_ingestor` / `owned_by_source`), `util/store_builders.py` (bucket → stores),
`util/model_builders.py` (bucket → configuration, models, vector width), `util/source_builders.py` (bucket → source
configuration, rclone remote), `util/source_updated_notifier.py` (announce written/removed files),
`util/partition_utils.py` (composite `{bucket}|{uri}` keys)

**Source pipeline form**: `source_pipelines/rclone_sync_config.py` (RcloneSyncConfig, six backends); base class
`SourcePipelineConfig` and `SourcePipelineEntity` live in `packages/core`

**Utilities**: `packages/pipeline/swiss_ai_hub/pipeline/util/` — definitions_util, id_utils, bucket_utils, key_utils

**Apps**: `app/document_ingestion_pipeline/__init__.py`, `app/rclone_pipeline/__init__.py`

**Playground**: `playground/__init__.py`, `playground/quick_start/`
