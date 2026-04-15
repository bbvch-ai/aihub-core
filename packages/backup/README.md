# swiss-ai-hub-backup

Backup and restore orchestration for AI-Hub data services. Runs as an independent Dagster instance (3 containers: gRPC
code server, daemon, webserver) inside the Docker Compose project.

Requires the Docker socket (`/var/run/docker.sock`) to discover and manage platform containers via the
`com.docker.compose.project` label.

Dagster UI: <http://localhost:3004>

## DocumentDB Catalog Maintenance

The PostgreSQL handler hardcodes DocumentDB extension catalog tables and sequences in `_DOCUMENTDB_CATALOG_TABLES` and
`_DOCUMENTDB_CATALOG_SEQUENCES` (`services/postgres.py`). After upgrading the DocumentDB extension, verify the list is
still complete:

```sql
SELECT c.relname, c.relkind FROM pg_class c
JOIN pg_depend d ON c.oid = d.objid
JOIN pg_extension e ON d.refobjid = e.oid
WHERE e.extname = 'documentdb' AND c.relkind IN ('r', 'S')
ORDER BY c.relkind, c.relname;
```

Run this against the `postgres` database on `postgres-ferretdb`. `relkind = 'r'` = tables, `'S'` = sequences.
