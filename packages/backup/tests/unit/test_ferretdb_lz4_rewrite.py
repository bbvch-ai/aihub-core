"""Unit tests for FerretdbLz4RewriteHandler: the PostgreSQL connection and the Mongo client are faked."""

from __future__ import annotations

from collections.abc import Iterator
from unittest.mock import MagicMock, patch

import pytest

from swiss_ai_hub.backup.maintenance.base import MaintenanceResult
from swiss_ai_hub.backup.maintenance.ferretdb_lz4_rewrite import FerretdbLz4RewriteHandler

pytestmark = pytest.mark.unit

_MODULE = "swiss_ai_hub.backup.maintenance.ferretdb_lz4_rewrite"


class _FakeConnection:
    """Answers the handler's SQL by statement text; pglz counts are consumed in order, before then after a rewrite."""

    def __init__(self, compression: str, tables: list[tuple[str, int]], pglz_counts: dict[int, list[int]]) -> None:
        self.compression = compression
        self.tables = tables
        self.pglz_counts = pglz_counts
        self.vacuumed: list[str] = []

    def execute(self, statement: object, params: dict[str, object] | None = None) -> MagicMock:
        sql = str(statement)
        result = MagicMock()
        if sql.startswith("SHOW default_toast_compression"):
            result.scalar_one.return_value = self.compression
        elif "documentdb_api_catalog.collections" in sql:
            result.all.return_value = self.tables
        elif sql.startswith("VACUUM"):
            self.vacuumed.append(sql)
        elif "pg_column_compression" in sql:
            collection_id = int(sql.split("documents_")[1].split()[0])
            result.scalar_one.return_value = self.pglz_counts[collection_id].pop(0)
        elif "pg_total_relation_size" in sql:
            result.scalar_one.return_value = 1000
        return result


@pytest.fixture
def mongo_collection() -> Iterator[MagicMock]:
    with patch(f"{_MODULE}.MongoClient") as mongo_client:
        collection = MagicMock()
        collection.find.return_value.sort.return_value = [{"_id": f"doc-{index}"} for index in range(120)]
        client = mongo_client.return_value.__enter__.return_value
        client.__getitem__.return_value.__getitem__.return_value = collection
        yield collection


def _run(connection: _FakeConnection) -> MaintenanceResult:
    with patch(f"{_MODULE}.build_ferretdb_engine") as build_engine:
        engine_connection = build_engine.return_value.connect.return_value.execution_options.return_value
        engine_connection.__enter__.return_value = connection
        return FerretdbLz4RewriteHandler(MagicMock()).run()


def test_refuses_to_run_while_the_server_still_compresses_with_pglz(mongo_collection: MagicMock) -> None:
    result = _run(_FakeConnection("pglz", [("kb", 11)], {11: [3, 0]}))

    assert not result.succeeded
    assert "default_toast_compression is pglz" in (result.error or "")
    mongo_collection.update_many.assert_not_called()


def test_rewrites_collections_with_pglz_rows_in_batches_and_skips_the_rest(mongo_collection: MagicMock) -> None:
    connection = _FakeConnection("lz4", [("finance", 11), ("legal", 12)], {11: [3, 0], 12: [0]})

    result = _run(connection)

    assert result.succeeded
    assert result.rows_affected == 120
    assert result.metadata["collections_seen"] == 2
    assert result.metadata["collections_skipped"] == 1
    assert result.metadata["collections_rewritten"] == "finance"
    assert (result.metadata["pglz_rows_before"], result.metadata["pglz_rows_after"]) == (3, 0)
    assert connection.vacuumed == ["VACUUM (ANALYZE) documentdb_data.documents_11"]
    updates = [call.args for call in mongo_collection.update_many.call_args_list]
    assert updates[0] == ({"_lz4_rewrite": {"$exists": True}}, {"$unset": {"_lz4_rewrite": ""}})
    batches = updates[1:]
    assert [len(update[0]["_id"]["$in"]) for update in batches[::2]] == [50, 50, 20]
    assert all(update[1] == {"$set": {"_lz4_rewrite": True}} for update in batches[::2])
    assert all(update[1] == {"$unset": {"_lz4_rewrite": ""}} for update in batches[1::2])
    assert [update[0] for update in batches[::2]] == [update[0] for update in batches[1::2]]


def test_a_second_run_skips_every_collection(mongo_collection: MagicMock) -> None:
    result = _run(_FakeConnection("lz4", [("finance", 11)], {11: [0]}))

    assert result.succeeded
    assert result.metadata["collections_rewritten"] == "none (no pglz rows left)"
    mongo_collection.update_many.assert_not_called()


def test_rows_still_pglz_after_the_rewrite_fail_the_run(mongo_collection: MagicMock) -> None:
    result = _run(_FakeConnection("lz4", [("finance", 11)], {11: [3, 2]}))

    assert not result.succeeded
    assert "2 rows are still pglz" in (result.error or "")
    assert result.metadata["pglz_rows_after"] == 2


def test_an_error_is_returned_not_raised(mongo_collection: MagicMock) -> None:
    mongo_collection.find.side_effect = RuntimeError("connection refused")

    result = _run(_FakeConnection("lz4", [("finance", 11)], {11: [3, 0]}))

    assert not result.succeeded
    assert result.error == "connection refused"


def test_vacuums_every_ten_batches_so_dead_versions_are_reused(mongo_collection: MagicMock) -> None:
    mongo_collection.find.return_value.sort.return_value = [{"_id": f"doc-{index}"} for index in range(1200)]
    connection = _FakeConnection("lz4", [("finance", 11)], {11: [1200, 0]})

    _run(connection)

    assert connection.vacuumed == [
        "VACUUM documentdb_data.documents_11",
        "VACUUM documentdb_data.documents_11",
        "VACUUM (ANALYZE) documentdb_data.documents_11",
    ]
