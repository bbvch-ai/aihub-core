"""Unit tests for FerretdbLz4RewriteHandler: the PostgreSQL connection is faked."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from swiss_ai_hub.backup.maintenance.base import MaintenanceResult
from swiss_ai_hub.backup.maintenance.ferretdb_lz4_rewrite import FerretdbLz4RewriteHandler

pytestmark = pytest.mark.unit

_MODULE = "swiss_ai_hub.backup.maintenance.ferretdb_lz4_rewrite"


class _FakeConnection:
    """Answers the handler's SQL by statement text; pglz counts are consumed in order, before then after a rewrite."""

    def __init__(
        self,
        compression: str,
        tables: list[tuple[str, str, int]],
        pglz_counts: dict[int, list[int]],
        keys: int = 120,
    ) -> None:
        self.compression = compression
        self.tables = tables
        self.pglz_counts = pglz_counts
        self.keys = keys
        self.updates: list[tuple[str, dict[str, list[object]]]] = []
        self.vacuumed: list[str] = []

    def execute(self, statement: object, params: dict[str, list[object]] | None = None) -> MagicMock:
        sql = str(statement)
        result = MagicMock()
        if sql.startswith("SHOW default_toast_compression"):
            result.scalar_one.return_value = self.compression
        elif "documentdb_api_catalog.collections" in sql:
            result.all.return_value = self.tables
        elif sql.startswith("VACUUM"):
            self.vacuumed.append(sql)
        elif sql.startswith("UPDATE"):
            self.updates.append((sql, params or {}))
            result.rowcount = len((params or {})["ids"])
        elif sql.startswith("SELECT shard_key_value"):
            result.all.return_value = [(7, f"id-{index}".encode()) for index in range(self.keys)]
        elif sql.startswith("SELECT count(*)"):
            collection_id = int(sql.split("documents_")[1].split()[0])
            result.scalar_one.return_value = self.pglz_counts[collection_id].pop(0)
        elif "pg_total_relation_size" in sql:
            result.scalar_one.return_value = 1000
        return result


def _run(connection: _FakeConnection) -> MaintenanceResult:
    with patch(f"{_MODULE}.build_ferretdb_engine") as build_engine:
        engine_connection = build_engine.return_value.connect.return_value.execution_options.return_value
        engine_connection.__enter__.return_value = connection
        return FerretdbLz4RewriteHandler(MagicMock()).run()


def test_refuses_to_run_while_the_server_still_compresses_with_pglz() -> None:
    connection = _FakeConnection("pglz", [("kb", "documents-data", 11)], {11: [3, 0]})

    result = _run(connection)

    assert not result.succeeded
    assert "default_toast_compression is pglz" in (result.error or "")
    assert connection.updates == []


def test_rewrites_every_collection_with_pglz_rows_in_batches_and_skips_the_rest() -> None:
    connection = _FakeConnection(
        "lz4",
        [("aihub", "agent_events", 11), ("aihub", "buckets", 12), ("finance", "documents-data", 13)],
        {11: [3, 0], 12: [0], 13: [5, 0]},
    )

    result = _run(connection)

    assert result.succeeded
    assert result.rows_affected == 240
    assert result.metadata["collections_seen"] == 3
    assert result.metadata["collections_skipped"] == 1
    assert result.metadata["collections_rewritten"] == "aihub.agent_events, finance.documents-data"
    assert (result.metadata["pglz_rows_before"], result.metadata["pglz_rows_after"]) == (8, 0)
    assert connection.vacuumed == [
        "VACUUM (ANALYZE) documentdb_data.documents_11",
        "VACUUM (ANALYZE) documentdb_data.documents_13",
    ]
    first_table = [params for sql, params in connection.updates if "documents_11" in sql]
    assert [len(params["ids"]) for params in first_table] == [50, 50, 20]
    assert all(params["shards"] == [7] * len(params["ids"]) for params in first_table)


def test_each_batch_only_touches_rows_that_are_still_pglz_and_keeps_their_bytes() -> None:
    connection = _FakeConnection("lz4", [("finance", "documents-data", 11)], {11: [1, 0]}, keys=1)

    _run(connection)

    sql = connection.updates[0][0]
    assert "pg_column_compression(d.document) = 'pglz'" in sql
    assert "bson_from_bytea(documentdb_core.bson_to_bytea(d.document))" in sql


def test_a_second_run_skips_every_collection() -> None:
    connection = _FakeConnection("lz4", [("finance", "documents-data", 11)], {11: [0]})

    result = _run(connection)

    assert result.succeeded
    assert result.metadata["collections_rewritten"] == "none (no pglz rows left)"
    assert connection.updates == []


def test_rows_still_pglz_after_the_rewrite_fail_the_run() -> None:
    result = _run(_FakeConnection("lz4", [("finance", "documents-data", 11)], {11: [3, 2]}))

    assert not result.succeeded
    assert "2 rows are still pglz" in (result.error or "")
    assert result.metadata["pglz_rows_after"] == 2


def test_an_error_is_returned_not_raised() -> None:
    connection = _FakeConnection("lz4", [("finance", "documents-data", 11)], {11: [3, 0]})
    connection.execute = MagicMock(side_effect=RuntimeError("connection refused"))

    result = _run(connection)

    assert not result.succeeded
    assert result.error == "connection refused"


def test_vacuums_every_ten_batches_so_dead_versions_are_reused() -> None:
    connection = _FakeConnection("lz4", [("finance", "documents-data", 11)], {11: [1200, 0]}, keys=1200)

    _run(connection)

    assert connection.vacuumed == [
        "VACUUM documentdb_data.documents_11",
        "VACUUM documentdb_data.documents_11",
        "VACUUM (ANALYZE) documentdb_data.documents_11",
    ]
