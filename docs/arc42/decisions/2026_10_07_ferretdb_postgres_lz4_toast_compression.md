# lz4 Compression for FerretDB's PostgreSQL

## Context

FerretDB stores every document as one BSON value in a PostgreSQL row, through the DocumentDB extension. PostgreSQL
compresses large values with `default_toast_compression`, which is `pglz` unless configured, and nothing configured it.
DocumentDB decompresses the whole value for every filter operator, projection and sort it evaluates. Knowledge rows
(`documents-data`) carry the parsed text twice, so the content search (#1024) and the document listing (#1948) spend
most of their time decompressing.

Measured at 5,000 documents × 100k characters:

| Query                       |      pglz |       lz4 |
| --------------------------- | --------: | --------: |
| Content search, no hit      | 2.6–2.8 s | 1.2–1.4 s |
| Content search, common term | 7.4–7.6 s | 2.4–2.5 s |
| Document listing            | 8.1–8.4 s | 1.8–2.3 s |

The table took 503 MB on lz4 against 496 MB on pglz. PostgreSQL records the method per stored value, so pglz and lz4
rows read correctly side by side. A value keeps its method until it changes: an identical write, or
`UPDATE … SET document = document`, copies the compressed bytes unchanged.

## Decision Drivers

- **Search latency**\
  The content search must answer within about 2 s at medium corpus size to be usable in an agent's tool loop.
- **Every collection, present and future**\
  New knowledge databases are created at runtime; the setting must not depend on knowing their tables.
- **Visible configuration**\
  The setting belongs in the compose template, not in state hidden in a data volume.
- **No content change**\
  Existing documents must keep their exact bytes and key order.

## Decision

1. `postgres-ferretdb` runs with `command: ["postgres", "-c", "default_toast_compression=lz4"]`. The image's command is
   plain `postgres`, and its DocumentDB settings live in the volume's `postgresql.conf`, so the flag adds to them.
2. The backup Dagster instance gets `ferretdb_lz4_rewrite_job`, launched by hand and never scheduled. It recompresses
   the pglz rows of **every** collection table in SQL, 50 rows at a time by primary key:
   `SET document = bson_from_bytea(bson_to_bytea(document)) WHERE pg_column_compression(document) = 'pglz'`. The round
   trip builds a new value with the same bytes, which PostgreSQL compresses with the new default. It runs `VACUUM` every
   500 rows so the replaced row versions' space is reused, and `VACUUM (ANALYZE)` at the end. It refuses to run while the
   server default is not lz4, and it skips collections that have no pglz rows left.

The rewrite writes DocumentDB's tables directly instead of going through FerretDB. A FerretDB-level rewrite would need a
visible change to each document (set a temporary field, then remove it). MongoEngine entities reject unknown fields
unless they opt out (`AgentConfigEntityDocument` does not), so a reader catching a row in between, or a run interrupted
in between, would break reads. Going through FerretDB was also about ten times slower per MB on the dev stack (258 s for
534 MB against 31 s for 690 MB). The SQL round trip changes no byte of any document, which the integration test
checks against raw BSON, and selecting only pglz rows makes an interrupted run resume where it stopped.

Rejected alternatives:

- **Per-column `ALTER TABLE … SET COMPRESSION lz4`**: misses every collection created afterwards.
- **`ALTER SYSTEM SET default_toast_compression`**: works, but lives only in the volume's `postgresql.auto.conf`, where
  no review or redeploy sees it.
- **Re-ingestion alone**: old documents that never change would stay pglz forever.
- **A `$set`/`$unset` rewrite through FerretDB**: see above.
- **Knowledge stores only**: the measured win is there, but agent events and configurations are read on every request
  too, and the SQL rewrite is cheap enough to cover everything once.

## Consequences

### Positive

- Content search and listing run 2–4× faster on lz4 rows, which brings the #1024 gate within reach.
- Every new or changed row in every collection is lz4, with no per-collection setup.
- Compression is faster too, and the disk cost is negligible.
- A restore writes rows with the target server's default, so restoring onto an lz4 server needs no rewrite.

### Trade-offs

- **Recreating `postgres-ferretdb`** on the first deploy makes FerretDB unavailable for a few seconds. A
  `docker restart` does not apply the flag; the container has to be recreated.
- **The rewrite job bypasses FerretDB.** It depends on DocumentDB's table layout (`documentdb_data.documents_<id>`,
  `shard_key_value`, `object_id`, `document`) and on `documentdb_core.bson_to_bytea`/`bson_from_bytea`. Re-check it
  against the integration test before running it after a DocumentDB upgrade.
- **The rewrite job's cost:**
  - one write per pglz row: 18,900 rows in 8 collections (690 MB) took 31 seconds on the dev stack;
  - the tables grow by about a tenth (690 to 761 MB) and keep that size, since plain VACUUM does not return space to the
    OS;
  - it competes for PostgreSQL's cache while it runs, and it holds the backup instance's Postgres mutex.
- **Future images must be built with lz4.** A server without it cannot read lz4 rows and refuses to start with the flag.
  Check `pg_config --configure | grep lz4` on every `postgres_ferretdb` image bump.
- **Rollback** is removing the flag. New rows are then pglz again, and lz4 rows stay readable, so nothing needs
  migrating back.
