import logging
import time
from typing import Annotated

import psycopg
from psycopg import errors, sql

from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_text_index_query import KnowledgeTextIndexQuery
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_text_index_settings import (
    KnowledgeTextIndexSettings,
)
from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn

logger = logging.getLogger(__name__)

# A term found in many documents, or a phrase whose words are all common, makes PostgreSQL recheck most rows, and its
# `ILIKE` is slower than FerretDB's regex scan. Past these bounds the index cannot win, so it gives up and the scan
# answers; a selective term stays far below them (tens of milliseconds, a handful of candidates).
MAX_INDEX_CANDIDATES = 500
MAX_INDEX_SECONDS = 0.5

# The backup's `ferretdb_text_index_job` creates the index under this name and stamps it with the DocumentDB version
# it was checked against; an index from before an upgrade is ignored until the job has checked and rebuilt it.
_USABLE_INDEX = sql.SQL(
    "SELECT c.collection_id FROM documentdb_api_catalog.collections c "
    "JOIN pg_class ix ON ix.relname = 'aihub_text_trgm_' || c.collection_id "
    "AND ix.relnamespace = 'documentdb_data'::regnamespace "
    "JOIN pg_index i ON i.indexrelid = ix.oid "
    "WHERE c.database_name = %(database)s AND c.collection_name = 'documents-data' "
    "AND i.indisvalid AND i.indisready "
    "AND obj_description(ix.oid, 'pg_class') = "
    "(SELECT 'documentdb_core ' || extversion FROM pg_extension WHERE extname = 'documentdb_core')"
)
# Must match the indexed expression exactly, or PostgreSQL cannot use the index. `object_id` holds `_id` alone, so
# reading it never decompresses the document.
_CANDIDATES = (
    "SELECT documentdb_core.bson_get_value_text(object_id, '') FROM {table} "
    "WHERE documentdb_core.bson_get_value_text(document, '__data__.text') {operator} ANY(%(patterns)s) "
    "LIMIT %(limit)s"
)
# The index path is an optimisation: a missing role, an unreachable server, a timeout or a DocumentDB that no longer
# has these objects all mean the scan answers instead.
_INDEX_UNUSABLE = (
    psycopg.OperationalError,
    errors.InsufficientPrivilege,
    errors.UndefinedTable,
    errors.UndefinedFunction,
)


class KnowledgeTextIndex:
    """Candidate documents for a literal content search, from the trigram index on each knowledge database's table.

    FerretDB cannot use an expression index: it evaluates `$regex` itself on every row. So this reads DocumentDB's
    tables directly, through a read-only role, and returns ids only; the caller asks FerretDB which of them match, so
    the result is exactly the scan's. A database whose index is missing, still building or not checked against the
    running DocumentDB version answers None, and so does every database when the index cannot be reached.
    """

    @staticmethod
    @trace_fn
    async def candidate_ids(
        db_names: Annotated[list[str], "Knowledge databases to look up, by their Mongo database name"],
        query: Annotated[KnowledgeTextIndexQuery, "The literal search as LIKE patterns"],
        timeout_seconds: Annotated[float, "Time the lookups may take in all, capped at `MAX_INDEX_SECONDS`"],
    ) -> dict[str, list[str] | None]:
        """Candidate ids per database, or None where the scan has to answer."""
        unusable: dict[str, list[str] | None] = dict.fromkeys(db_names)
        settings = KnowledgeTextIndexSettings()
        if not settings.enabled or not db_names:
            return unusable
        timeout_seconds = min(timeout_seconds, MAX_INDEX_SECONDS)
        deadline = time.monotonic() + timeout_seconds
        try:
            async with await psycopg.AsyncConnection.connect(
                host=settings.HOST,
                port=settings.PORT,
                dbname=settings.DATABASE,
                user=settings.USER,
                password=settings.PASSWORD.get_secret_value(),
                connect_timeout=1,
                application_name="swiss-ai-hub-content-search",
            ) as connection:
                return {
                    db_name: await KnowledgeTextIndex._candidates_in(connection, db_name, query, deadline)
                    for db_name in db_names
                }
        except _INDEX_UNUSABLE as unusable_error:
            logger.warning("Content search falls back to the scan: %s", unusable_error)
            return unusable

    @staticmethod
    async def _candidates_in(
        connection: psycopg.AsyncConnection,
        db_name: str,
        query: KnowledgeTextIndexQuery,
        deadline: float,
    ) -> list[str] | None:
        """The planner underestimates how selective a trigram condition is and would scan the table, which is what
        the index exists to avoid, so sequential scans are switched off for this one query. Running out of time is
        the expected answer for a common term, so it is not logged."""
        timeout_ms = int((deadline - time.monotonic()) * 1000)
        if timeout_ms <= 0:
            return None
        try:
            rows = await KnowledgeTextIndex._query(connection, db_name, query, timeout_ms)
        except errors.QueryCanceled:
            return None
        return None if rows is None else KnowledgeTextIndex._ids(rows)

    @staticmethod
    async def _query(
        connection: psycopg.AsyncConnection, db_name: str, query: KnowledgeTextIndexQuery, timeout_ms: int
    ) -> list[tuple[str | None]] | None:
        async with connection.transaction():
            index = await (await connection.execute(_USABLE_INDEX, {"database": db_name})).fetchone()
            if index is None:
                return None
            await connection.execute("SELECT set_config('enable_seqscan', 'off', true)")
            await connection.execute("SELECT set_config('statement_timeout', %s, true)", (str(timeout_ms),))
            statement = sql.SQL(_CANDIDATES).format(
                table=sql.Identifier("documentdb_data", f"documents_{int(index[0])}"),
                operator=sql.SQL("LIKE" if query.case_sensitive else "ILIKE"),
            )
            return await (
                await connection.execute(statement, {"patterns": query.patterns, "limit": MAX_INDEX_CANDIDATES + 1})
            ).fetchall()

    @staticmethod
    def _ids(rows: list[tuple[str | None]]) -> list[str] | None:
        """Ids come back as their JSON text, a string id in quotes; any other id type cannot be matched against the
        ids FerretDB returns, so the scan answers."""
        if len(rows) > MAX_INDEX_CANDIDATES:
            return None
        ids = []
        for (value,) in rows:
            if value is None or len(value) < 2 or not value.startswith('"') or not value.endswith('"'):
                return None
            ids.append(value[1:-1])
        return ids
