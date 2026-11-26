import json
import logging
import time
from typing import override

from sqlalchemy import Connection, text

from swiss_ai_hub.backup.maintenance.base import MaintenanceHandler, MaintenanceResult
from swiss_ai_hub.backup.maintenance.postgres_engine import build_ferretdb_engine
from swiss_ai_hub.backup.settings import BackupSettings

logger = logging.getLogger(__name__)
_LABEL = "ferretdb_text_index"
_REBUILD_LABEL = "ferretdb_text_index_rebuild"
# The content search (packages/core, KnowledgeTextIndex) uses an index only under this name and only while its comment
# names the running DocumentDB version; change both sides together.
_INDEX_PREFIX = "aihub_text_trgm_"
_STAMP_PREFIX = "documentdb_core "
# The content search's login role, created by the ferretdb-init container. It reads only the tables indexed here,
# never the rest of FerretDB's data.
TEXT_SEARCH_ROLE = "aihub_text_search"
_TEXT_EXPRESSION = "documentdb_core.bson_get_value_text(document, '__data__.text')"
# Everything the content search relies on: a string comes back whole, wrapped in quotes and with nothing escaped, so a
# `LIKE '%term%'` on the result finds exactly what a search of the text finds.
_CANARY_TEXT = 'Käse "zitiert" C:\\Pfad\ttab\r\nzweite Zeile 😀 Ka\u0308se µg'
_TABLES_SQL = text(
    "SELECT c.collection_id, c.database_name, ix.oid IS NOT NULL AS has_index, "
    "COALESCE(i.indisvalid AND i.indisready, false) AS is_valid, obj_description(ix.oid, 'pg_class') AS stamp "
    "FROM documentdb_api_catalog.collections c "
    "LEFT JOIN pg_class ix ON ix.relname = :prefix || c.collection_id "
    "AND ix.relnamespace = 'documentdb_data'::regnamespace "
    "LEFT JOIN pg_index i ON i.indexrelid = ix.oid "
    "WHERE c.collection_name = 'documents-data' AND c.view_definition IS NULL "
    "AND to_regclass('documentdb_data.documents_' || c.collection_id) IS NOT NULL "
    "ORDER BY c.database_name"
)


class FerretdbTextIndexHandler(MaintenanceHandler):
    """Keep a trigram index on every knowledge database's parsed text, for the literal content search.

    The index is built on DocumentDB's table with `CREATE INDEX CONCURRENTLY`, so FerretDB keeps reading and writing
    while it builds; a build that was interrupted leaves an invalid index, which the next run drops and builds again.
    It indexes the output of a DocumentDB function, which an upgrade could change without notice. So every run first
    checks that function against a known value and stops if it differs, and each index is stamped with the
    DocumentDB version it was built under; the content search ignores an index whose stamp is not the running
    version, and this handler rebuilds such an index before stamping it again. `rebuild` rebuilds every index, which
    only reclaims space. See docs/arc42/decisions/2026_10_08_trigram_index_for_knowledge_content_search.md.
    """

    def __init__(self, settings: BackupSettings, rebuild: bool = False) -> None:
        self._settings = settings
        self._rebuild = rebuild

    @property
    @override
    def service_name(self) -> str:
        return _REBUILD_LABEL if self._rebuild else _LABEL

    @override
    def run(self) -> MaintenanceResult:
        start = time.monotonic()
        try:
            engine = build_ferretdb_engine(self._settings)
            with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
                version = conn.execute(
                    text("SELECT extversion FROM pg_extension WHERE extname = 'documentdb_core'")
                ).scalar_one()
                canary_error = self._canary_error(conn)
                if canary_error:
                    return self._failed(start, canary_error, {"documentdb_core": version})
                metadata = self._maintain_all(conn, f"{_STAMP_PREFIX}{version}")
        except Exception as e:
            return self._failed(start, str(e))
        return MaintenanceResult(
            name=self.service_name,
            succeeded=True,
            duration_seconds=round(time.monotonic() - start, 1),
            metadata={"documentdb_core": version, **metadata},
        )

    @staticmethod
    def _canary_error(conn: Connection) -> str | None:
        document = json.dumps({"__data__": {"text": _CANARY_TEXT}})
        extracted = conn.execute(
            text(f"SELECT {_TEXT_EXPRESSION} FROM (SELECT CAST(:document AS documentdb_core.bson) AS document) AS d"),
            {"document": document},
        ).scalar_one()
        expected = f'"{_CANARY_TEXT}"'
        if extracted == expected:
            return None
        return (
            f"bson_get_value_text returned {extracted!r} for {_CANARY_TEXT!r}, expected {expected!r}: DocumentDB "
            "changed how it extracts text, so no index is stamped and the content search keeps scanning. Check "
            "KnowledgeTextIndexQuery against the new output before adapting the canary"
        )

    def _maintain_all(self, conn: Connection, stamp: str) -> dict[str, str | int | float]:
        tables = conn.execute(_TABLES_SQL, {"prefix": _INDEX_PREFIX}).all()
        reader_exists = conn.execute(
            text("SELECT 1 FROM pg_roles WHERE rolname = :role"), {"role": TEXT_SEARCH_ROLE}
        ).first()
        actions: dict[str, list[str]] = {"created": [], "rebuilt": [], "unchanged": []}
        for collection_id, database_name, has_index, is_valid, current_stamp in tables:
            index = f"{_INDEX_PREFIX}{int(collection_id)}"
            action = self._maintain(conn, int(collection_id), has_index, is_valid, current_stamp == stamp)
            if action != "unchanged" or current_stamp != stamp:
                self._execute_formatted(conn, "COMMENT ON INDEX documentdb_data.%I IS %L", index, stamp)
            if reader_exists:
                self._execute_formatted(
                    conn,
                    "GRANT SELECT ON documentdb_data.%I TO %I",
                    f"documents_{int(collection_id)}",
                    TEXT_SEARCH_ROLE,
                )
            actions[action].append(database_name)
            if action != "unchanged":
                logger.info("[%s] %s the text index of %s", self.service_name, action.capitalize(), database_name)
        return {
            "knowledge_databases": len(tables),
            "read_access_granted_to": TEXT_SEARCH_ROLE
            if reader_exists
            else f"nobody: role {TEXT_SEARCH_ROLE} is missing",
            **{action: ", ".join(names) if names else "none" for action, names in actions.items()},
        }

    @staticmethod
    def _execute_formatted(conn: Connection, template: str, *identifiers_and_literals: str) -> None:
        """Statements that take no bind parameters, with names and values quoted by PostgreSQL's `format()`."""
        placeholders = ", ".join(f"CAST(:a{position} AS text)" for position in range(len(identifiers_and_literals)))
        statement = conn.execute(
            text(f"SELECT format(:template, {placeholders})"),
            {"template": template, **{f"a{i}": value for i, value in enumerate(identifiers_and_literals)}},
        ).scalar_one()
        conn.execute(text(statement))

    def _maintain(self, conn: Connection, collection_id: int, has_index: bool, is_valid: bool, is_stamped: bool) -> str:
        """A stamp from another DocumentDB version means the index may hold another function's output: rebuild."""
        index = f"documentdb_data.{_INDEX_PREFIX}{collection_id}"
        if has_index and not is_valid:
            conn.execute(text(f"DROP INDEX CONCURRENTLY IF EXISTS {index}"))
            has_index = False
        if not has_index:
            conn.execute(
                text(
                    f"CREATE INDEX CONCURRENTLY IF NOT EXISTS {_INDEX_PREFIX}{collection_id} "
                    f"ON documentdb_data.documents_{collection_id} USING gin (({_TEXT_EXPRESSION}) gin_trgm_ops)"
                )
            )
            return "created"
        if self._rebuild or not is_stamped:
            conn.execute(text(f"REINDEX INDEX CONCURRENTLY {index}"))
            return "rebuilt"
        return "unchanged"

    def _failed(
        self, start: float, error: str, metadata: dict[str, str | int | float] | None = None
    ) -> MaintenanceResult:
        logger.error("[%s] %s", self.service_name, error)
        return MaintenanceResult(
            name=self.service_name,
            succeeded=False,
            duration_seconds=round(time.monotonic() - start, 1),
            error=error,
            metadata=metadata or {},
        )
