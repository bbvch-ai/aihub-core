# Structured Sources Are Synced with dlt into Markdown Files

## Context

Confluence pages, Jira issues and similar sources are API records, not files. The rclone source pipeline
(`2026_09_09_source_pipelines_as_a_second_axis_of_a_knowledge_database`) cannot sync them: it copies files from a remote
into a database's data lake, and these sources have no files to copy. Issue
[#1890](https://github.com/bbvch-ai/aihub-core/issues/1890) asks for a second source pipeline type that turns records
into markdown files with YAML frontmatter in the database's data lake. The unchanged ingestion pipeline then parses,
chunks and embeds them, and [#1953](https://github.com/bbvch-ai/aihub-core/issues/1953) turns the frontmatter into
document metadata. The Jira and Confluence adapters themselves are
[#1954](https://github.com/bbvch-ai/aihub-core/issues/1954) and
[#1955](https://github.com/bbvch-ai/aihub-core/issues/1955).

The source-pipelines ADR already fixes most of the shape. A source pipeline announces a `SourcePipelineConfig` form, the
API validates and encrypts what a database stores, one deployment serves every database whose `source` names it, the
target database is resolved per run, and the pipeline never touches the doc or vector store. The open question was which
tool reads the records, and how a tool built for warehouse loading behaves when the "warehouse" is a bucket of markdown
files, one database at a time, in a Dagster deployment whose steps are fresh processes.

The evaluation ran as a throwaway spike, never merged: dlt 1.30.0 and dagster-dlt 0.29.23 against Dagster 1.13.23 and
Python 3.13, a fake issue tracker, S3 provided by moto, and every sync run in a fresh process with a fresh dlt working
directory, as a Dagster step runs under `DefaultRunLauncher`. The evidence is recorded at the end of this document.

## Decision Drivers

- **A new source kind must cost an adapter, not a client library.**\
  Jira and Confluence are the first two of many record sources. Pagination, authentication, rate-limit back-off and
  incremental cursors are the same problem for each, and should be solved once.
- **One deployment, N databases, with different credentials.**\
  Inherited from the source-pipelines ADR. Nothing about a database's source may be fixed at `Definitions`-build time,
  and two databases syncing the same kind must never share state, files or credentials.
- **Incremental syncs whose state survives the process.**\
  Re-reading every Jira issue every day is not acceptable for large projects. The sync state must outlive the step
  process and the container, because neither is kept.
- **A run with no changes at the source writes nothing.**\
  Every written file is announced to the ingestion pipeline, so a spurious write costs a parse and an embedding.
- **Deletions at the source must reach the database.**\
  A record deleted or moved out of scope at the source must disappear from the database after the next run.
- **Python, in process, configured per call.**\
  The pipeline already resolves configuration per run from the database row. A tool that needs a project file, a
  separate virtual environment per connector or process-wide environment variables fights that model.

## Alternatives Considered

1. **Meltano (Singer taps and targets).** Rejected. Every tap and target is installed into its own virtual environment
   and runs as a separate process. It is configured through a `meltano.yml` project and `<PLUGIN>_<SETTING>` environment
   variables, so per-run configuration from a database row means generating a project per run. Writing markdown means
   writing a Singer target. Its Dagster integration, `dagster-meltano`, is community-maintained. Its last release was in
   October 2024, and it requires Python below 3.13, so it does not install in our pipeline image.

2. **PyAirbyte (Airbyte connectors in Python).** Rejected. It is licensed under the Elastic License 2.0, which forbids
   providing the software to third parties as a hosted or managed service. That does not fit an open-source platform
   that others host and operate. It also requires Python below 3.13, and it runs connectors in their own virtual
   environments or Docker containers (`airbyte-source-jira` requires Python below 3.12). The full Airbyte platform,
   which `dagster-airbyte` orchestrates, would be a separate deployment of its own.

3. **LlamaIndex readers (`llama-index-readers-jira`, `llama-index-readers-confluence`).** Rejected. They are MIT
   licensed, run in process and return documents close to what we need, but every call reads everything in scope. They
   keep no cursor and no state, so we would build incremental syncs ourselves, as with our own clients, on top of a
   reader that was not designed for it. The Confluence reader also logs and skips a page it fails to process unless
   `fail_on_error` is set, and a page silently missing from a sync would be deleted by the listing of decision 6.

4. **Our own API clients per source.** Rejected, narrowly. There is no new framework: `httpx` is already a dependency,
   and we would have full control. But every adapter re-implements pagination, retries, rate-limit back-off and
   incremental cursors, including de-duplicating records that share the cursor's boundary timestamp. That is the work
   driver 1 says should be done once. Persisting the state is ours to build under either option (decision 5), so what
   dlt saves is exactly that client-side machinery, and this is the alternative to revisit if dlt ever gets in the way.

5. **dlt through `@dlt_assets`, the integration's primary entry point.** Rejected. The decorator binds one source and
   one pipeline when definitions load, and derives one asset per dlt resource. Here the source kind and its credentials
   are chosen per run from the database row, and an asset per resource would be shared by every database that uses the
   kind.

6. **One Dagster run per record, the rclone shape.** Rejected. rclone partitions per file so that one bad file fails
   alone. A Jira project has thousands of issues, which would mean thousands of runs per database per day, each fetching
   its record a second time, while dlt fetches a page of changed records in one request.

7. **dlt's own state handling.** Rejected, because it does not work here. dlt restores state from the destination, and a
   custom destination has nowhere to keep it. dlt's documentation says so: "Custom destinations lack a general mechanism
   to restore pipeline state". The local working directory is lost with the step process.

## Decision

**A `structured` source pipeline runs dlt sources and writes their records as markdown files through a dlt custom
destination. It is a second source pipeline type under the source-pipelines ADR, and nothing about how a database is
configured, secured or ingested changes.**

1. **One code location, one token, one form.** `structured_pipeline_definitions(source="structured")` builds the code
   location, shaped like `rclone_pipeline_definitions`. Every Dagster name derives from the token, and
   `SourcePipelineType.STRUCTURED` reserves it against ingestors. `StructuredSyncConfig(SourcePipelineConfig)` has a
   `source_kind` select and one option group per kind, shown through `condition_if`, as `RcloneSyncConfig` does for its
   backends. Credentials are `str | Password` fields, so the API encrypts and masks them as it does for rclone.

2. **An adapter per source kind** declares:

   - its options form
   - the dlt source it runs, incremental on the record's last update
   - how one record becomes a file: a path, frontmatter and body
   - how to list the path of every record currently in scope

   Records become files in the extract step (`add_map`), not in the destination: dlt normalises rows before loading,
   coercing ISO timestamps to `pendulum.DateTime`, which YAML cannot render. The first path segment is the namespace,
   and a path without a folder is rejected, because the ingestion pipeline never ingests a root-level object.
   Frontmatter uses the reserved keys of #1953 (`title`, `url`, `created`, `updated`) and renders deterministically,
   with sorted keys. Adding a kind is one adapter, one options form, one field on `StructuredSyncConfig` and its labels,
   with no change to the API or the UI.

3. **One sync run per database per day.** `per_bucket_observe_schedule(owns=owned_by_source("structured"))` fans out one
   run per database, tagged `aihub/bucket`. The run is one `graph_asset` whose ops are, in order:

   - sync the changed records
   - list every current path
   - reconcile: the files to remove are those the bucket holds, minus the listed paths, minus the files this run wrote
   - remove and announce them, reusing `delete_data_lake_files_from_bucket` and `announce_removed_files` unchanged

   dlt runs through dagster-dlt's `DagsterDltResource.run(context, dlt_source=…, dlt_pipeline=…)`, which the integration
   documents for ops. Its materialization events name an asset per dlt resource, shared by all databases, so the op
   folds their metadata (`rows_loaded`, `jobs`, timings) into the run's own asset instead of emitting them.

4. **The destination writes only what changed.** For each file it compares the MD5 of the content with the ETag of the
   object already in the bucket. It writes only on a difference, then announces the written keys through
   `notify_source_updated`. dlt delivers at least once, since a failed load job is retried and a lost state re-delivers
   everything, so this comparison is what makes "no changes writes nothing" hold. The ETag is used rather than a hash of
   our own kept as object metadata, because the ingestion pipeline copies a file's metadata into its document and embeds
   it with every chunk. A multipart ETag is not an MD5 and never matches, so such a file is simply rewritten; records
   are far below the multipart threshold.

5. **State is one small file per database, kept by us.** Each run creates its dlt pipeline as `{source}_{bucket}` in a
   fresh temporary working directory. It restores `state.json` (about 1 KB, holding the incremental cursors) from
   `s3://{bucket}/.{source}_dagster/state.json` before the run, and writes it back **only after the sync has
   succeeded**, and only while the database still uses this source. The file lives in the database's own bucket, not in
   the `dagster` bucket: that bucket expires its objects after a day, data-lake listings skip `.…dagster` folders, and
   teardown deletes the file together with the bucket, so no cleanup sensor is needed. A fingerprint of the non-secret
   configuration and the adapter's `layout_version` is kept with it. When the scope or the layout changes, for example a
   project key is added, the run does a full refresh, because the old cursor would skip everything older in the new
   scope. Rotating credentials keeps the state.

6. **Deletions are found by listing, after the sync.** dlt has no way to detect a record deleted at the source when it
   loads incrementally. After every successful sync, the adapter lists every path currently in scope, and whatever the
   bucket holds beyond that is removed and announced. The comparison covers the whole bucket, which is correct because a
   sourced database is filled by its source alone.

7. **Credentials travel as arguments.** The decrypted configuration from `source_config_for_bucket` is passed to the
   adapter's dlt source as call arguments, never through dlt's configuration providers (environment variables,
   `secrets.toml`), which are shared by the whole process.

8. **Switching a database between two sources needs the same acknowledgement as giving a manual database a source.**
   With two source types, rclone → structured is a real switch, and the new source's first removal pass deletes every
   file the old one wrote. `PUT /knowledge/databases/{database}/source` therefore requires `replace_existing_documents`
   on any change of source while the database holds documents, not only from manual upload, and the UI asks before it
   sends it. Editing the current source's settings saves without asking, since the admin is changing that source's own
   scope; switching back to manual upload removes nothing and needs nothing.

### Rules that are not optional

Rules 1 and 2 guard failures the spike reproduced. Rules 3 to 7 follow from how Dagster stores outputs, from the order
of the steps and from the state being one file. All seven failures are silent: the run succeeds, and the damage shows up
later as missing documents, a database emptied by mistake, or a full re-read nobody notices.

1. **Turn off `restore_from_destination` on every pipeline.** When it is on, which is dlt's default,
   `DagsterDltResource` calls `pipeline.drop()` before every run. That deletes the state just restored, and every run
   silently re-reads the whole source. The ETag check hides it: nothing is written, but the run fetches everything.

2. **Back up the state only after the run has succeeded.** dlt advances the cursor in the local `state.json` during
   extraction, before loading. In the spike, a load that failed left the local cursor past two records that never
   reached the bucket. Backing that file up would skip them forever.

3. **Never pass the listing from one asset to another.** The default IO manager stores a non-partitioned asset's output
   at one path per asset key, under `s3://dagster/structured/`. That path is shared by every database, and the daily
   schedule starts every database's run in the same minute, so one database's removal could read another's listing and
   empty itself. Sync, listing and removal stay ops inside one `graph_asset`, whose intermediate outputs are stored per
   run.

4. **List after the sync, never before.** A record written by the sync but missing from an earlier listing is deleted as
   an orphan, and never comes back, because the cursor has already moved past it.

5. **A failed listing raises, it never returns empty.** An empty listing removes every file in the database. Wrong
   credentials must fail the run, as they already do in the sync step, before any removal. An empty listing while the
   bucket holds files fails the run too.

6. **A listed record without a file discards the state.** The cursor is then ahead of the data, after a lost file, a
   source switch or a layout change, and would never fetch that record again. The next run re-reads everything, and the
   ETag check keeps it from rewriting what is already there.

7. **One sync per database at a time.** Two runs of the same database would race on its state file. A run that finds
   another sync of the same database running gives way, whichever was created first.

## Consequences

### Positive

- A database picks a structured source kind in the UI, enters its configuration and syncs on the next scheduled run,
  with no deployment change, exactly as an rclone database does.
- A new record source costs one adapter. Pagination, retries and incremental cursors come from dlt, and dlt's REST API
  source declares most of them.
- Credentials never leave the encrypted row except as call arguments in the step process. The spike found no credential
  in the dlt working directory or in the backed-up state.
- The dependency footprint is small. `dlt` and `dagster-dlt` add 13 transitive packages, none of them pyarrow or duckdb,
  and change no existing pin.

### Trade-offs

- **dlt brings no ready-made Jira or Confluence connector.** The verified Jira source has no incremental cursor, and
  there is no verified Confluence source. #1954 and #1955 build their adapters on dlt's REST API source, which declares
  pagination, authentication and incremental cursors.
- **A sync is daily.** This is inherited from the source-pipelines ADR. Creating a database or changing its source
  triggers nothing, so a new database stays empty until the next scheduled run. A first-sync or on-demand trigger is a
  follow-up; the guard against two concurrent runs of the same database (rule 7) is already in place for it.
- **Deletion detection costs a full key listing per database per run**, on top of the incremental fetch. For Jira this
  is a paged search that returns only keys, and it is the price of driver 5.
- **dagster-dlt contributes little in this shape.** It runs the pipeline, drops pending load packages and produces the
  metadata. Its asset-per-resource model is not used. If it ever gets in the way, calling `pipeline.run()` directly
  changes nothing else in this decision.
- **Losing the state is safe but expensive.** Deleting a database's state file makes the next run re-read every record.
  The ETag check keeps writes and announcements at zero. It also happens without anyone deleting anything: a record
  created at the source while a run is between its fetch and its listing is listed without a file (rule 6), so on a busy
  source an occasional night is a full re-read.
- **A failing write is retried inside the run.** dlt retries a failed load job up to five times and re-delivers its
  batch each time, before the run fails. The ETag check makes the re-delivery harmless. A permanent error raises
  `DestinationTerminalException` so it fails at once.
- **The code location needs outbound internet access.** The rclone code location reaches its sources through the rclone
  daemon and sits only on `backend`, `data` and `storage`. This one calls the source APIs itself, so it also joins
  `egress`.
- **Frontmatter is plain text until #1953 lands.** Until then the ingestion pipeline chunks and embeds it like any
  paragraph.

## Related Decisions

- `2026_09_09_source_pipelines_as_a_second_axis_of_a_knowledge_database`: the source axis, registration, per-run
  resolution and secret handling this pipeline reuses unchanged.
- `2026_09_04_ingestors_announce_their_configuration_form`: the announced-form mechanism behind `StructuredSyncConfig`.
- `2026_06_18_rag_pipeline_route_per_run`: one deployment serving every database, resolved per run.
- `2026_09_14_secret_mask_carries_identity_handle`: how the masked credentials in the source form are restored.

## Spike Evidence

dlt 1.30.0, dagster-dlt 0.29.23, Dagster 1.13.23, Python 3.13.15. Resolving both packages against `uv.lock` added 15
packages (the two plus 13 transitive) and changed none; `dlt` itself is 6.2 MB. Every sync ran in a fresh process with a
fresh working directory, against a fake tracker and S3 from moto.

| Check                                                      | Result                                                                                       |
| ---------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| First sync, two databases, same kind, other credentials    | 3 and 2 files, each only in its own bucket; same record key in both kept apart               |
| Second run, no change at the source                        | 0 rows reached the destination, 0 writes; cursor restored from the 1 KB `state.json` alone   |
| One record edited                                          | 1 row, 1 write                                                                               |
| State deleted, everything re-delivered                     | 3 rows reached the destination, 0 writes (hash check)                                        |
| Record deleted at the source                               | Removed by the listing after the sync                                                        |
| Write fails mid-load                                       | Load retried 5 times in the run, then failed; local cursor had already advanced; backup kept |
| Next run after that failure                                | Both changed records re-fetched; the one already written skipped, the missing one written    |
| Wrong credentials                                          | Run fails in extract with the API's 401 message; no file removed                             |
| Credential set in the environment for the same key         | Explicit argument wins                                                                       |
| Rendering in the destination instead of in extract         | Fails: ISO timestamp arrives as `pendulum.DateTime`, which `yaml.safe_dump` cannot represent |
| Credential in the working directory or the backed-up state | Not found                                                                                    |
| `DagsterDltResource.run` from an op in a `graph_asset`     | Works; emits a `MaterializeResult` for `dlt_<source>_<resource>`                             |
| Same, with `restore_from_destination` left at its default  | Restored state dropped; every record re-fetched on every run                                 |
