import logging
import time
from typing import override

from pymongo import MongoClient
from pymongo.collection import Collection
from sqlalchemy import Connection, text

from swiss_ai_hub.backup.maintenance.base import MaintenanceHandler, MaintenanceResult
from swiss_ai_hub.backup.maintenance.postgres_engine import build_ferretdb_engine
from swiss_ai_hub.backup.settings import BackupSettings

logger = logging.getLogger(__name__)
_LABEL = "ferretdb_lz4_rewrite"
# The collection RefDoc rows live in, one per knowledge database; content search and listing scan it.
_KNOWLEDGE_COLLECTION = "documents-data"
_MARKER = "_lz4_rewrite"
_BATCH_SIZE = 50
# Every write leaves the old row version behind; vacuuming this often lets later batches reuse that space, where one
# VACUUM at the end let the table grow by most of its size.
_VACUUM_EVERY_BATCHES = 10
_KNOWLEDGE_TABLES_SQL = text(
    "SELECT database_name, collection_id FROM documentdb_api_catalog.collections "
    "WHERE collection_name = :collection ORDER BY database_name"
)


class FerretdbLz4RewriteHandler(MaintenanceHandler):
    """Recompress the knowledge doc stores' existing rows with lz4, once, after the server default moved to it.

    PostgreSQL keeps a stored value's compression until the value changes; an identical write or
    `UPDATE … SET document = document` copies it unchanged. Setting a temporary top-level field and unsetting it
    again through FerretDB gives a new value with the same content and key order, which the server compresses with
    its current default. Collections without pglz rows are skipped, so a second run is cheap. See
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
            with (
                build_ferretdb_engine(self._settings).connect().execution_options(isolation_level="AUTOCOMMIT") as conn,
                MongoClient(
                    host=self._settings.FERRETDB_HOST,
                    port=self._settings.FERRETDB_PORT,
                    username=self._settings.MONGO_USERNAME,
                    password=self._settings.MONGO_PASSWORD.get_secret_value(),
                ) as client,
            ):
                compression = conn.execute(text("SHOW default_toast_compression")).scalar_one()
                if compression != "lz4":
                    return self._failed(
                        start,
                        f"default_toast_compression is {compression}, not lz4: the rewrite would compress the rows "
                        "with it again. Recreate postgres-ferretdb with the lz4 flag first",
                    )
                metadata = self._rewrite_all(conn, client)
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

    def _rewrite_all(self, conn: Connection, client: MongoClient) -> dict[str, str | int | float]:
        tables = conn.execute(_KNOWLEDGE_TABLES_SQL, {"collection": _KNOWLEDGE_COLLECTION}).all()
        counts = {"pglz_rows_before": 0, "pglz_rows_after": 0, "rows_rewritten": 0, "bytes_before": 0, "bytes_after": 0}
        rewritten: list[str] = []
        for database_name, collection_id in tables:
            table = f"documentdb_data.documents_{int(collection_id)}"
            pglz_rows = self._pglz_rows(conn, table)
            if pglz_rows == 0:
                continue
            counts["pglz_rows_before"] += pglz_rows
            counts["bytes_before"] += self._size(conn, table)
            counts["rows_rewritten"] += self._rewrite(conn, table, client[database_name][_KNOWLEDGE_COLLECTION])
            counts["pglz_rows_after"] += self._pglz_rows(conn, table)
            counts["bytes_after"] += self._size(conn, table)
            rewritten.append(database_name)
            logger.info("[%s] Rewrote %s (%d pglz rows)", _LABEL, database_name, pglz_rows)
        return {
            "collections_seen": len(tables),
            "collections_skipped": len(tables) - len(rewritten),
            "collections_rewritten": ", ".join(rewritten) if rewritten else "none (no pglz rows left)",
            **counts,
        }

    @staticmethod
    def _rewrite(conn: Connection, table: str, collection: Collection) -> int:
        """Two writes per batch of ids, so no row keeps the temporary field; a field left by an interrupted run is
        removed first."""
        collection.update_many({_MARKER: {"$exists": True}}, {"$unset": {_MARKER: ""}})
        ids = [row["_id"] for row in collection.find({}, {"_id": 1}).sort("_id", 1)]
        for batch_number, index in enumerate(range(0, len(ids), _BATCH_SIZE), start=1):
            batch = {"_id": {"$in": ids[index : index + _BATCH_SIZE]}}
            collection.update_many(batch, {"$set": {_MARKER: True}})
            collection.update_many(batch, {"$unset": {_MARKER: ""}})
            if batch_number % _VACUUM_EVERY_BATCHES == 0:
                conn.execute(text(f"VACUUM {table}"))
        conn.execute(text(f"VACUUM (ANALYZE) {table}"))
        return len(ids)

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
