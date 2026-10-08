"""FerretdbLz4RewriteHandler against the dev stack's FerretDB and its PostgreSQL.

Needs `postgres-ferretdb` running with `default_toast_compression=lz4` and FerretDB on localhost:27017. The handler's
table listing is narrowed to a throwaway database, so the stack's own collections are left alone.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from pathlib import Path

import docker
import pytest
from bson.raw_bson import RawBSONDocument
from docker.errors import DockerException
from dotenv import dotenv_values
from pydantic import SecretStr
from pymongo import MongoClient
from pymongo.database import Database
from sqlalchemy import Engine, text

from swiss_ai_hub.backup.maintenance import ferretdb_lz4_rewrite
from swiss_ai_hub.backup.maintenance.ferretdb_lz4_rewrite import FerretdbLz4RewriteHandler
from swiss_ai_hub.backup.maintenance.postgres_engine import build_ferretdb_engine
from swiss_ai_hub.backup.settings import BackupSettings

pytestmark = pytest.mark.integration

_REPO_ROOT = Path(__file__).resolve().parents[4]
_COLLECTIONS = ("documents-data", "agent_events")
_ROWS = 12


def _settings_and_mongo() -> tuple[BackupSettings, MongoClient]:
    env = dotenv_values(_REPO_ROOT / ".env")
    try:
        container = docker.from_env().containers.get("postgres-ferretdb")
    except DockerException as error:
        pytest.skip(f"postgres-ferretdb is not running: {error}")
    address = next(iter(container.attrs["NetworkSettings"]["Networks"].values()))["IPAddress"]
    username, password = env.get("MONGO_USERNAME") or "admin", env.get("MONGO_PASSWORD") or ""
    settings = BackupSettings(
        POSTGRES_PASSWORD=SecretStr("unused"),
        MILVUS_ROOT_PASSWORD=SecretStr("unused"),
        LANGFUSE_CLICKHOUSE_PASSWORD=SecretStr("unused"),
        REDIS_TOKEN=SecretStr("unused"),
        NATS_TOKEN=SecretStr("unused"),
        S3_STORAGE_SECRET_KEY=SecretStr("unused"),
        POSTGRES_FERRETDB_HOST=address,
        MONGO_USERNAME=username,
        MONGO_PASSWORD=SecretStr(password),
    )
    return settings, MongoClient(host="127.0.0.1", port=27017, username=username, password=password)


def _document(index: int) -> dict[str, object]:
    """About 60 KB of repetitive text, so PostgreSQL compresses it, with mixed types to pin byte identity."""
    words = " ".join(f"Rechnung {index} Lieferung Prüfbericht Zeile {line}" for line in range(1500))
    return {"_id": f"doc-{index}", "n": index, "f": 1.5, "big": 2**40, "nested": {"a": [1, "x", None]}, "text": words}


@pytest.fixture
def pglz_database(monkeypatch: pytest.MonkeyPatch) -> Iterator[tuple[BackupSettings, Engine, Database]]:
    settings, client = _settings_and_mongo()
    engine = build_ferretdb_engine(settings)
    with engine.connect() as conn:
        if conn.execute(text("SHOW default_toast_compression")).scalar_one() != "lz4":
            pytest.skip("postgres-ferretdb does not run with default_toast_compression=lz4")
    database = client[f"lz4test_{uuid.uuid4().hex[:8]}"]
    monkeypatch.setattr(
        ferretdb_lz4_rewrite,
        "_TABLES_SQL",
        text(
            "SELECT database_name, collection_name, collection_id FROM documentdb_api_catalog.collections "
            f"WHERE database_name = '{database.name}' ORDER BY collection_name"
        ),
    )
    for name in _COLLECTIONS:
        database[name].insert_one({"_id": "seed"})
        table = _table(engine, database.name, name)
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            conn.execute(text(f"ALTER TABLE {table} ALTER COLUMN document SET COMPRESSION pglz"))
            database[name].insert_many([_document(index) for index in range(_ROWS)])
            conn.execute(text(f"ALTER TABLE {table} ALTER COLUMN document SET COMPRESSION DEFAULT"))
    yield settings, engine, database
    client.drop_database(database.name)
    client.close()


def _table(engine: Engine, database_name: str, collection_name: str) -> str:
    with engine.connect() as conn:
        collection_id = conn.execute(
            text(
                "SELECT collection_id FROM documentdb_api_catalog.collections "
                "WHERE database_name = :database AND collection_name = :collection"
            ),
            {"database": database_name, "collection": collection_name},
        ).scalar_one()
    return f"documentdb_data.documents_{collection_id}"


def _compression_counts(engine: Engine, database: Database, collection_name: str) -> dict[str | None, int]:
    table = _table(engine, database.name, collection_name)
    with engine.connect() as conn:
        rows = conn.execute(text(f"SELECT pg_column_compression(document), count(*) FROM {table} GROUP BY 1")).all()
    return {compression: count for compression, count in rows}


def _raw(database: Database) -> dict[tuple[str, str], bytes]:
    raw = {}
    for name in _COLLECTIONS:
        collection = database[name].with_options(
            codec_options=database[name].codec_options.with_options(document_class=RawBSONDocument)
        )
        raw |= {(name, document["_id"]): document.raw for document in collection.find({})}
    return raw


def test_rewrites_pglz_rows_of_every_collection_as_lz4_without_changing_a_byte(
    pglz_database: tuple[BackupSettings, Engine, Database],
) -> None:
    settings, engine, database = pglz_database
    assert all(_compression_counts(engine, database, name).get("pglz") == _ROWS for name in _COLLECTIONS)
    before = _raw(database)

    result = FerretdbLz4RewriteHandler(settings).run()

    assert result.succeeded, result.error
    assert result.rows_affected == 2 * _ROWS
    assert (result.metadata["pglz_rows_before"], result.metadata["pglz_rows_after"]) == (2 * _ROWS, 0)
    assert all(_compression_counts(engine, database, name).get("lz4") == _ROWS for name in _COLLECTIONS)
    assert _raw(database) == before
    assert database["agent_events"].count_documents({"n": {"$gte": 6}}) == 6


def test_a_second_run_skips_every_collection(pglz_database: tuple[BackupSettings, Engine, Database]) -> None:
    settings, _, _ = pglz_database
    FerretdbLz4RewriteHandler(settings).run()

    second = FerretdbLz4RewriteHandler(settings).run()

    assert second.succeeded, second.error
    assert second.metadata["collections_rewritten"] == "none (no pglz rows left)"
    assert second.rows_affected == 0


def test_an_interrupted_run_resumes_with_the_rows_still_pglz(
    pglz_database: tuple[BackupSettings, Engine, Database],
) -> None:
    settings, engine, database = pglz_database
    table = _table(engine, database.name, "documents-data")
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        conn.execute(
            text(
                f"UPDATE {table} "
                "SET document = documentdb_core.bson_from_bytea(documentdb_core.bson_to_bytea(document)) "
                f"WHERE ctid IN (SELECT ctid FROM {table} WHERE pg_column_compression(document) = 'pglz' LIMIT 5)"
            )
        )

    result = FerretdbLz4RewriteHandler(settings).run()

    assert result.succeeded, result.error
    assert result.rows_affected == 2 * _ROWS - 5
    assert _compression_counts(engine, database, "documents-data").get("pglz") is None
