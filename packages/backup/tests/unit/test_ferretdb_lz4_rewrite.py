"""Unit tests for FerretdbLz4RewriteHandler: the PostgreSQL connection is faked."""

from __future__ import annotations

from typing import Any
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
        self.updates: list[tuple[str, dict[str, Any]]] = []
        self.key_queries: list[tuple[str, dict[str, Any]]] = []
        self.vacuumed: list[str] = []

    def execute(self, statement: object, params: dict[str, Any] | None = None) -> MagicMock:
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
        elif sql.startswith("SELECT documentdb_core.bson_to_bytea(object_id)"):
            self.key_queries.append((sql, params or {}))
            keys = [f"id-{index:05d}".encode() for index in range(self.keys)]
            after = (params or {})["after"]
            result.scalars.return_value = [key for key in keys if after is None or key > after][: params["limit"]]
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
    assert all(params["shard_key_value"] == 11 for params in first_table)


def test_each_batch_continues_after_the_last_key_of_the_previous_one_by_primary_key() -> None:
    connection = _FakeConnection("lz4", [("finance", "documents-data", 11)], {11: [120, 0]}, keys=120)

    _run(connection)

    assert [params["after"] for _, params in connection.key_queries] == [None, b"id-00049", b"id-00099", b"id-00119"]
    first_page, next_page = connection.key_queries[0][0], connection.key_queries[1][0]
    assert "OPERATOR(documentdb_core.>)" not in first_page
    assert "shard_key_value = :shard_key_value AND object_id OPERATOR(documentdb_core.>)" in next_page
    update = connection.updates[0][0]
    assert "shard_key_value = :shard_key_value AND object_id OPERATOR(documentdb_core.=) ANY (" in update


def test_each_batch_only_touches_rows_that_are_still_pglz_and_keeps_their_bytes() -> None:
    connection = _FakeConnection("lz4", [("finance", "documents-data", 11)], {11: [1, 0]}, keys=1)

    _run(connection)

    sql = connection.updates[0][0]
    assert "pg_column_compression(document) = 'pglz'" in sql
    assert "bson_from_bytea(documentdb_core.bson_to_bytea(document))" in sql


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


def test_a_large_collection_vacuums_every_two_percent_of_its_pglz_rows_instead() -> None:
    """30,000 pglz rows: 2% is 600 rows, 12 batches, so 60 batches vacuum five times rather than six."""
    connection = _FakeConnection("lz4", [("finance", "documents-data", 11)], {11: [30_000, 0]}, keys=3_000)

    _run(connection)

    assert connection.vacuumed == ["VACUUM documentdb_data.documents_11"] * 5 + [
        "VACUUM (ANALYZE) documentdb_data.documents_11"
    ]
