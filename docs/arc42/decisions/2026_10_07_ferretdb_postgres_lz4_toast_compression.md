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
2. The backup Dagster instance gets `ferretdb_lz4_rewrite_job`, launched by hand and never scheduled. It rewrites the
   rows of every `documents-data` collection that still has pglz rows. It sets a temporary top-level field and unsets it
   again through FerretDB, in batches of 50, with a `VACUUM` every 500 rows so the replaced row versions' space is
   reused, and `VACUUM (ANALYZE)` at the end. It refuses to run while the
   server default is not lz4, and it skips collections that have no pglz rows left.

Rejected alternatives:

- **Per-column `ALTER TABLE … SET COMPRESSION lz4`**: misses every collection created afterwards.
- **`ALTER SYSTEM SET default_toast_compression`**: works, but lives only in the volume's `postgresql.auto.conf`, where
  no review or redeploy sees it.
- **Re-ingestion alone**: old documents that never change would stay pglz forever.
- **A job over every FerretDB collection**: the measured win is in the knowledge stores; other collections convert as
  their rows are written.

## Consequences

### Positive

- Content search and listing run 2–4× faster on lz4 rows, which brings the #1024 gate within reach.
- Every new or changed row in every collection is lz4, with no per-collection setup.
- Compression is faster too, and the disk cost is negligible.
- A restore writes rows with the target server's default, so restoring onto an lz4 server needs no rewrite.

### Trade-offs

- **Recreating `postgres-ferretdb`** on the first deploy makes FerretDB unavailable for a few seconds. A
  `docker restart` does not apply the flag; the container has to be recreated.
- **Rows outside the knowledge stores** stay pglz until they are written again. They read correctly, just slower.
- **The rewrite job's cost:**
  - write load and WAL of about twice each rewritten table: 5,400 rows (534 MB) took 4.3 minutes on the dev stack;
  - the tables grow by about a quarter (534 to 673 MB) and keep that size, since plain VACUUM does not return space to
    the OS. A single VACUUM at the end let them grow by 84%;
  - it holds the backup instance's Postgres mutex while it runs.
- **Future images must be built with lz4.** A server without it cannot read lz4 rows and refuses to start with the flag.
  Check `pg_config --configure | grep lz4` on every `postgres_ferretdb` image bump.
- **Rollback** is removing the flag. New rows are then pglz again, and lz4 rows stay readable, so nothing needs
  migrating back.
