# Bounded Retry of Failed Document Ingestion, Counted per Pipeline Version

## Context

The ingestion pipeline materializes a document's `documents`, `nodes` and `summary_nodes` partitions with
`AutomationCondition.eager()`, which fires when the file's data version (`{updated}-{hash}`) changes. A failed run
changes nothing, so a failed document never ran again: its partition stayed failed, the knowledge list showed it as
"Processing" like a document still in flight, and the only way out was re-uploading the same bytes to bump the file's
modification time. That is what happened after a bug in `chunk_ref_doc_into_nodes` was fixed: the documents it had
failed stayed failed.

## Decision Drivers

- **A failure is retried without the file changing**, and a fixed pipeline bug recovers what it failed, with no
  re-upload.
- **A deterministic failure stops.** An unparseable file or a model that rejects every chunk must not run every tick.
- **The knowledge list tells a failed document from one in progress.**
- **No new state store.** The platform already has two convergent work queues read by sensors (`deleting` for teardown,
  `classification_requested_at` for the classification backfill), with run keys numbered by attempt.

## Decision

1. **A sensor, not an automation condition.** `FailedIngestionRetrySensorFor_{ingestor}` reads each asset's partition
   statuses from Dagster's status cache (one call per asset) and, for every partition of a database this ingestor
   owns, takes the earliest asset that failed. It requests that asset alone, so automation carries the rest of the chain
   as it does for a new file. An automation condition has no per-partition attempt count, which a bound needs.
2. **A failure starts at the latest run the sensor did not request.** That is the automation run a new or changed file
   triggered, or a run launched by hand. Retries tag their runs with that origin, so a file that changes and fails again
   starts over.
3. **The budget is counted per pipeline version.** Retries carry the installed `swiss-ai-hub-pipeline` version, and only
   retries of the current version count against `DOCUMENT_INGESTION_MAX_RETRIES` (3). A release therefore retries every
   document an earlier one gave up on, which is how a bug fix recovers its documents. A document that cannot be ingested
   costs at most that many runs per release.
4. **Backoff.** A retry waits `DOCUMENT_INGESTION_RETRY_BACKOFF_MINUTES` (10) after the latest attempt ended. Retries
   run at priority -1, below new uploads and observations, and at most 50 are requested per tick.
5. **The sensor writes the failure to the document's record.** `RefDoc.record_ingestion_failure` sets
   `ingestion_failed_attempts`, `ingestion_failed_at` and `ingestion_gave_up` on a pending document only, and only
   when the record is dated strictly before the failed attempt started (to the second, rounded down): a re-upload
   resets and re-dates the record, even while the old run is still going, and until its new run starts Dagster still
   reports the old failure, which that run never saw. A successful parse rewrites the record, `mark_ingested` and a
   re-upload clear the fields, and so does the sensor while a run it did not request is queued or running, which is
   what resets a file that changed at its source. A synced file that never parsed has no record, so the sensor
   inserts a placeholder carrying the failure (`create_failed_placeholder`); placeholders are insert-only, because
   MongoEngine's `save()` of a document with an id replaces any record holding it. The API derives `ingestion_state`
   (`ingested`, `processing`, `retrying`, `failed`) from them.
6. **No manual "reprocess" action.** With the budget per version, the case it was meant for (a fixed bug) recovers by
   itself. An outage longer than the retries also leaves documents failed until the next release or a re-upload;
   a per-document action can follow if that proves common.

## Consequences

- `processing` covers both waiting for and running an attempt. Telling them apart would need a write when a run starts,
  and a successful parse rewrites the whole record.
- A fix shipped without a version bump (a local rebuild) grants no new budget; re-upload, or launch the partition by
  hand, which starts a new failure.
- After a release, every given-up document is retried once more, at low priority, up to 50 per minute.
- The knowledge list stops polling a failed row, so a row whose file changed at its source shows `processing` only
  after a reload.
- The sensor reads all unfinished runs once per tick, and up to 100 runs per failed partition. Given-up partitions are read every tick until their file
  changes or the next release.
