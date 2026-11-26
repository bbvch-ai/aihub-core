"""FerretdbTextIndexHandler against the dev stack's FerretDB and its PostgreSQL.

Needs `postgres-ferretdb` and FerretDB on localhost:27017. The handler's table listing is narrowed to a throwaway
knowledge database, so the stack's own indexes are left alone.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from pathlib import Path

import docker
import pytest
from docker.errors import DockerException
from dotenv import dotenv_values
from pydantic import SecretStr
from pymongo import MongoClient
from sqlalchemy import Connection, text

from swiss_ai_hub.backup.maintenance import ferretdb_text_index
from swiss_ai_hub.backup.maintenance.ferretdb_text_index import TEXT_SEARCH_ROLE, FerretdbTextIndexHandler
from swiss_ai_hub.backup.maintenance.postgres_engine import build_ferretdb_engine
from swiss_ai_hub.backup.settings import BackupSettings

pytestmark = pytest.mark.integration

_REPO_ROOT = Path(__file__).resolve().parents[4]


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


@pytest.fixture
def knowledge_database(monkeypatch: pytest.MonkeyPatch) -> Iterator[tuple[BackupSettings, Connection, str]]:
    settings, client = _settings_and_mongo()
    database_name = f"textindextest_{uuid.uuid4().hex[:8]}"
    client[database_name]["documents-data"].insert_many(
        [{"_id": f"doc-{index}", "__data__": {"text": f"Rechnung {index} der Zeta Dynamics AG"}} for index in range(5)]
    )
    narrowed = ferretdb_text_index._TABLES_SQL.text.replace(
        "ORDER BY", f"AND c.database_name = '{database_name}' ORDER BY"
    )
    monkeypatch.setattr(ferretdb_text_index, "_TABLES_SQL", text(narrowed))
    engine = build_ferretdb_engine(settings)
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        yield settings, conn, database_name
    client.drop_database(database_name)
    client.close()


def _index_state(conn: Connection, database_name: str) -> tuple[int, bool, str | None]:
    collection_id = conn.execute(
        text(
            "SELECT collection_id FROM documentdb_api_catalog.collections "
            "WHERE database_name = :name AND collection_name = 'documents-data'"
        ),
        {"name": database_name},
    ).scalar_one()
    row = conn.execute(
        text(
            "SELECT i.indisvalid, obj_description(i.indexrelid, 'pg_class') FROM pg_index i "
            "JOIN pg_class c ON c.oid = i.indexrelid WHERE c.relname = :index"
        ),
        {"index": f"aihub_text_trgm_{collection_id}"},
    ).one()
    return collection_id, row[0], row[1]


def _current_stamp(conn: Connection) -> str:
    version = conn.execute(text("SELECT extversion FROM pg_extension WHERE extname = 'documentdb_core'")).scalar_one()
    return f"documentdb_core {version}"


def test_creates_and_stamps_the_index_then_leaves_it_alone(
    knowledge_database: tuple[BackupSettings, Connection, str],
) -> None:
    settings, conn, database_name = knowledge_database

    first = FerretdbTextIndexHandler(settings).run()
    second = FerretdbTextIndexHandler(settings).run()

    assert first.succeeded, first.error
    assert (first.metadata["created"], second.metadata["unchanged"]) == (database_name, database_name)
    _, is_valid, stamp = _index_state(conn, database_name)
    assert (is_valid, stamp) == (True, _current_stamp(conn))


def test_an_index_stamped_by_another_documentdb_version_is_rebuilt(
    knowledge_database: tuple[BackupSettings, Connection, str],
) -> None:
    settings, conn, database_name = knowledge_database
    FerretdbTextIndexHandler(settings).run()
    collection_id, _, _ = _index_state(conn, database_name)
    conn.execute(text(f"COMMENT ON INDEX documentdb_data.aihub_text_trgm_{collection_id} IS 'documentdb_core 0.0-0'"))

    result = FerretdbTextIndexHandler(settings).run()

    assert result.metadata["rebuilt"] == database_name
    assert _index_state(conn, database_name)[2] == _current_stamp(conn)


def test_an_interrupted_build_is_dropped_and_built_again(
    knowledge_database: tuple[BackupSettings, Connection, str],
) -> None:
    """An interrupted CREATE INDEX CONCURRENTLY leaves the index marked invalid, as simulated here."""
    settings, conn, database_name = knowledge_database
    FerretdbTextIndexHandler(settings).run()
    collection_id, _, _ = _index_state(conn, database_name)
    conn.execute(
        text(
            "UPDATE pg_index SET indisvalid = false "
            f"WHERE indexrelid = 'documentdb_data.aihub_text_trgm_{collection_id}'::regclass"
        )
    )

    result = FerretdbTextIndexHandler(settings).run()

    assert result.metadata["created"] == database_name
    assert _index_state(conn, database_name)[1:] == (True, _current_stamp(conn))


def test_rebuild_rebuilds_a_current_index(knowledge_database: tuple[BackupSettings, Connection, str]) -> None:
    settings, _, database_name = knowledge_database
    FerretdbTextIndexHandler(settings).run()

    result = FerretdbTextIndexHandler(settings, rebuild=True).run()

    assert (result.name, result.metadata["rebuilt"]) == ("ferretdb_text_index_rebuild", database_name)


def test_a_changed_text_extraction_stops_the_run_before_any_index_is_touched(
    monkeypatch: pytest.MonkeyPatch, knowledge_database: tuple[BackupSettings, Connection, str]
) -> None:
    settings, conn, database_name = knowledge_database
    monkeypatch.setattr(
        ferretdb_text_index,
        "_TEXT_EXPRESSION",
        "upper(documentdb_core.bson_get_value_text(document, '__data__.text'))",
    )

    result = FerretdbTextIndexHandler(settings).run()

    assert not result.succeeded
    assert "changed how it extracts text" in (result.error or "")
    with pytest.raises(Exception, match="No row was found"):
        _index_state(conn, database_name)


def test_the_search_role_may_read_the_indexed_table(knowledge_database: tuple[BackupSettings, Connection, str]) -> None:
    settings, conn, database_name = knowledge_database
    if conn.execute(text("SELECT 1 FROM pg_roles WHERE rolname = :role"), {"role": TEXT_SEARCH_ROLE}).first() is None:
        pytest.skip(f"{TEXT_SEARCH_ROLE} does not exist; ferretdb-init has not run")

    FerretdbTextIndexHandler(settings).run()

    collection_id, _, _ = _index_state(conn, database_name)
    assert conn.execute(
        text("SELECT has_table_privilege(:role, :table, 'SELECT')"),
        {"role": TEXT_SEARCH_ROLE, "table": f"documentdb_data.documents_{collection_id}"},
    ).scalar_one()
