"""FerretdbLz4RewriteHandler against the dev stack's FerretDB and its PostgreSQL.

Needs `postgres-ferretdb` running with `default_toast_compression=lz4` and FerretDB on localhost:27017. The handler is
pointed at a collection name of its own, so the stack's real knowledge doc stores are left alone.
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
from pymongo.collection import Collection
from sqlalchemy import Engine, text

from swiss_ai_hub.backup.maintenance import ferretdb_lz4_rewrite
from swiss_ai_hub.backup.maintenance.ferretdb_lz4_rewrite import FerretdbLz4RewriteHandler
from swiss_ai_hub.backup.maintenance.postgres_engine import build_ferretdb_engine
from swiss_ai_hub.backup.settings import BackupSettings

pytestmark = pytest.mark.integration

_REPO_ROOT = Path(__file__).resolve().parents[4]
_ROWS = 12


def _settings() -> BackupSettings:
    env = dotenv_values(_REPO_ROOT / ".env")
    try:
        container = docker.from_env().containers.get("postgres-ferretdb")
    except DockerException as error:
        pytest.skip(f"postgres-ferretdb is not running: {error}")
    address = next(iter(container.attrs["NetworkSettings"]["Networks"].values()))["IPAddress"]
    return BackupSettings(
        POSTGRES_PASSWORD=SecretStr("unused"),
        MILVUS_ROOT_PASSWORD=SecretStr("unused"),
        LANGFUSE_CLICKHOUSE_PASSWORD=SecretStr("unused"),
        REDIS_TOKEN=SecretStr("unused"),
        NATS_TOKEN=SecretStr("unused"),
        S3_STORAGE_SECRET_KEY=SecretStr("unused"),
        POSTGRES_FERRETDB_HOST=address,
        FERRETDB_HOST="127.0.0.1",
        MONGO_USERNAME=env.get("MONGO_USERNAME") or "admin",
        MONGO_PASSWORD=SecretStr(env.get("MONGO_PASSWORD") or ""),
    )


def _document(index: int) -> dict[str, object]:
    """About 60 KB of repetitive text, so PostgreSQL compresses it, with nested fields to pin key order."""
    words = " ".join(f"Rechnung {index} Lieferung Prüfbericht Zeile {line}" for line in range(1500))
    return {"_id": f"doc-{index}", "__data__": {"text": words, "metadata": {"source": f"f{index}.md", "n": index}}}


@pytest.fixture
def pglz_collection(monkeypatch: pytest.MonkeyPatch) -> Iterator[tuple[BackupSettings, Engine, Collection]]:
    settings = _settings()
    engine = build_ferretdb_engine(settings)
    with engine.connect() as conn:
        if conn.execute(text("SHOW default_toast_compression")).scalar_one() != "lz4":
            pytest.skip("postgres-ferretdb does not run with default_toast_compression=lz4")
    collection_name = f"documents-data-lz4test-{uuid.uuid4().hex[:8]}"
    monkeypatch.setattr(ferretdb_lz4_rewrite, "_KNOWLEDGE_COLLECTION", collection_name)
    database_name = f"lz4test_{uuid.uuid4().hex[:8]}"
    client = MongoClient(
        host=settings.FERRETDB_HOST,
        port=settings.FERRETDB_PORT,
        username=settings.MONGO_USERNAME,
        password=settings.MONGO_PASSWORD.get_secret_value(),
    )
    collection = client[database_name][collection_name]
    collection.insert_one({"_id": "seed"})
    table = _table(engine, database_name, collection_name)
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        conn.execute(text(f"ALTER TABLE {table} ALTER COLUMN document SET COMPRESSION pglz"))
        collection.insert_many([_document(index) for index in range(_ROWS)])
        conn.execute(text(f"ALTER TABLE {table} ALTER COLUMN document SET COMPRESSION DEFAULT"))
    yield settings, engine, collection
    client.drop_database(database_name)
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


def _compression_counts(engine: Engine, collection: Collection) -> dict[str | None, int]:
    table = _table(engine, collection.database.name, collection.name)
    with engine.connect() as conn:
        rows = conn.execute(text(f"SELECT pg_column_compression(document), count(*) FROM {table} GROUP BY 1")).all()
    return {compression: count for compression, count in rows}


def _raw(collection: Collection) -> dict[str, bytes]:
    raw = collection.with_options(codec_options=collection.codec_options.with_options(document_class=RawBSONDocument))
    return {document["_id"]: document.raw for document in raw.find({})}


def test_rewrites_pglz_rows_as_lz4_without_changing_a_byte(
    pglz_collection: tuple[BackupSettings, Engine, Collection],
) -> None:
    settings, engine, collection = pglz_collection
    assert _compression_counts(engine, collection).get("pglz") == _ROWS
    before = _raw(collection)

    result = FerretdbLz4RewriteHandler(settings).run()

    assert result.succeeded, result.error
    assert result.rows_affected == _ROWS + 1
    assert (result.metadata["pglz_rows_before"], result.metadata["pglz_rows_after"]) == (_ROWS, 0)
    assert _compression_counts(engine, collection).get("lz4") == _ROWS
    assert _raw(collection) == before
    assert collection.count_documents({"_lz4_rewrite": {"$exists": True}}) == 0


def test_a_second_run_skips_the_rewritten_collection(
    pglz_collection: tuple[BackupSettings, Engine, Collection],
) -> None:
    settings, _, _ = pglz_collection
    FerretdbLz4RewriteHandler(settings).run()

    second = FerretdbLz4RewriteHandler(settings).run()

    assert second.succeeded, second.error
    assert second.metadata["collections_rewritten"] == "none (no pglz rows left)"
    assert second.rows_affected == 0


def test_a_field_left_by_an_interrupted_run_is_removed(
    pglz_collection: tuple[BackupSettings, Engine, Collection],
) -> None:
    settings, _, collection = pglz_collection
    collection.update_one({"_id": "doc-0"}, {"$set": {"_lz4_rewrite": True}})

    result = FerretdbLz4RewriteHandler(settings).run()

    assert result.succeeded, result.error
    assert collection.count_documents({"_lz4_rewrite": {"$exists": True}}) == 0
