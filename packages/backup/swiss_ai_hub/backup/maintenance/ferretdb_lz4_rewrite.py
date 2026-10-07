import logging
import time
from typing import override

from sqlalchemy import Connection, text

from swiss_ai_hub.backup.maintenance.base import MaintenanceHandler, MaintenanceResult
from swiss_ai_hub.backup.maintenance.postgres_engine import build_ferretdb_engine
from swiss_ai_hub.backup.settings import BackupSettings

logger = logging.getLogger(__name__)
_LABEL = "ferretdb_lz4_rewrite"
_BATCH_SIZE = 50
# Every write leaves the old row version behind; vacuuming this often lets later batches reuse that space, where one
# VACUUM at the end let the table grow by most of its size.
_VACUUM_EVERY_BATCHES = 10
_TABLES_SQL = text(
    "SELECT database_name, collection_name, collection_id FROM documentdb_api_catalog.collections "
    "WHERE view_definition IS NULL AND to_regclass('documentdb_data.documents_' || collection_id) IS NOT NULL "
    "ORDER BY database_name, collection_name"
)


class FerretdbLz4RewriteHandler(MaintenanceHandler):
    """Recompress every FerretDB collection's pglz rows with lz4, once, after the server default moved to it.

    PostgreSQL keeps a stored value's compression until the value is replaced, and `UPDATE … SET document = document`
    copies the compressed bytes unchanged. Passing the document through `bson_to_bytea` and back builds a new value
    with the same bytes, which the server compresses with its current default. It runs in SQL against DocumentDB's
    tables rather than through FerretDB, so no reader ever sees a changed document, and it only touches rows that are
    still pglz, so an interrupted run resumes where it stopped and a finished one is a no-op. See
    docs/arc42/decisions/2026_10_07_ferretdb_postgres_lz4_toast_compression.md.
    """

    def __init__(self, settings: BackupSettings) -> None:
        self._settings = settings

    @property
    @override
    def service_name(self) -> str:
        return _LABEL

    @override
    def run(self) -> MaintenanceResult:
        start = time.monotonic()
        try:
            engine = build_ferretdb_engine(self._settings)
            with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
                compression = conn.execute(text("SHOW default_toast_compression")).scalar_one()
                if compression != "lz4":
                    return self._failed(
                        start,
                        f"default_toast_compression is {compression}, not lz4: the rewrite would compress the rows "
                        "with it again. Recreate postgres-ferretdb with the lz4 flag first",
                    )
                metadata = self._rewrite_all(conn)
        except Exception as e:
            return self._failed(start, str(e))
        if metadata["pglz_rows_after"]:
            return self._failed(start, f"{metadata['pglz_rows_after']} rows are still pglz after the rewrite", metadata)
        return MaintenanceResult(
            name=_LABEL,
            succeeded=True,
            duration_seconds=round(time.monotonic() - start, 1),
            rows_affected=int(metadata["rows_rewritten"]),
            metadata=metadata,
        )

    def _rewrite_all(self, conn: Connection) -> dict[str, str | int | float]:
        tables = conn.execute(_TABLES_SQL).all()
        counts = {"pglz_rows_before": 0, "pglz_rows_after": 0, "rows_rewritten": 0, "bytes_before": 0, "bytes_after": 0}
        rewritten: list[str] = []
        for database_name, collection_name, collection_id in tables:
            table = f"documentdb_data.documents_{int(collection_id)}"
            pglz_rows = self._pglz_rows(conn, table)
            if pglz_rows == 0:
                continue
            counts["pglz_rows_before"] += pglz_rows
            counts["bytes_before"] += self._size(conn, table)
            counts["rows_rewritten"] += self._rewrite(conn, table)
            counts["pglz_rows_after"] += self._pglz_rows(conn, table)
            counts["bytes_after"] += self._size(conn, table)
            rewritten.append(f"{database_name}.{collection_name}")
            logger.info("[%s] Rewrote %s.%s (%d pglz rows)", _LABEL, database_name, collection_name, pglz_rows)
        return {
            "collections_seen": len(tables),
            "collections_skipped": len(tables) - len(rewritten),
            "collections_rewritten": ", ".join(rewritten) if rewritten else "none (no pglz rows left)",
            **counts,
        }

    @staticmethod
    def _rewrite(conn: Connection, table: str) -> int:
        """Rows are addressed by their primary key, and each batch rechecks that a row is still pglz, so a row that
        FerretDB replaced meanwhile is left as written. DocumentDB's bson operators are outside the search path, hence
        the qualified `OPERATOR(documentdb_core.=)`."""
        keys = conn.execute(
            text(
                f"SELECT shard_key_value, documentdb_core.bson_to_bytea(object_id) FROM {table} "
                "WHERE pg_column_compression(document) = 'pglz' ORDER BY shard_key_value, object_id"
            )
        ).all()
        rewritten = 0
        for batch_number, index in enumerate(range(0, len(keys), _BATCH_SIZE), start=1):
            batch = keys[index : index + _BATCH_SIZE]
            rewritten += conn.execute(
                text(
                    f"UPDATE {table} AS d "
                    "SET document = documentdb_core.bson_from_bytea(documentdb_core.bson_to_bytea(d.document)) "
                    "FROM (SELECT unnest(CAST(:shards AS bigint[])) AS shard_key_value, "
                    "documentdb_core.bson_from_bytea(unnest(CAST(:ids AS bytea[]))) AS object_id) AS batch "
                    "WHERE d.shard_key_value = batch.shard_key_value "
                    "AND d.object_id OPERATOR(documentdb_core.=) batch.object_id "
                    "AND pg_column_compression(d.document) = 'pglz'"
                ),
                {"shards": [shard for shard, _ in batch], "ids": [object_id for _, object_id in batch]},
            ).rowcount
            if batch_number % _VACUUM_EVERY_BATCHES == 0:
                conn.execute(text(f"VACUUM {table}"))
        conn.execute(text(f"VACUUM (ANALYZE) {table}"))
        return rewritten

    @staticmethod
    def _pglz_rows(conn: Connection, table: str) -> int:
        """Reads each value's compression header, not the value itself."""
        return conn.execute(
            text(f"SELECT count(*) FROM {table} WHERE pg_column_compression(document) = 'pglz'")
        ).scalar_one()

    @staticmethod
    def _size(conn: Connection, table: str) -> int:
        return conn.execute(
            text("SELECT pg_total_relation_size(CAST(:table AS regclass))"), {"table": table}
        ).scalar_one()

    @staticmethod
    def _failed(start: float, error: str, metadata: dict[str, str | int | float] | None = None) -> MaintenanceResult:
        logger.error("[%s] %s", _LABEL, error)
        return MaintenanceResult(
            name=_LABEL,
            succeeded=False,
            duration_seconds=round(time.monotonic() - start, 1),
            error=error,
            metadata=metadata or {},
        )
