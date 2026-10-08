"""The content search's index path against the stack's FerretDB and the PostgreSQL behind it.

Needs `postgres-ferretdb` reachable at `KNOWLEDGE_TEXT_INDEX_HOST`/`PORT` with the admin credentials in `MONGO_USERNAME`
and `MONGO_PASSWORD`. The fixture builds the index of its own knowledge database the way `ferretdb_text_index_job`
does and creates the read-only role the way `ferretdb-init` does, so it does not depend on either having run.
"""

import os
import unicodedata
import uuid
from collections.abc import Iterator

import psycopg
import pytest
from mongoengine import connect, disconnect
from mongoengine.connection import get_db
from psycopg import sql

from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_content_search import KnowledgeContentSearch
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_text_index import KnowledgeTextIndex
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_text_index_query import KnowledgeTextIndexQuery
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_text_index_settings import (
    KnowledgeTextIndexSettings,
)
from swiss_ai_hub.core.generative_ai.knowledge_documents.tests.integration.knowledge_document_seeder import (
    KnowledgeDocumentSeeder,
)
from swiss_ai_hub.core.generative_ai.retrievers.bucket_namespace_pair import BucketNamespacePair
from swiss_ai_hub.core.infrastructure.api.ai_hub_settings import AIHubSettings
from swiss_ai_hub.core.infrastructure.mongo.mongo_connection_registry import MongoConnectionRegistry
from swiss_ai_hub.core.infrastructure.mongo.mongo_settings import MongoSettings
from swiss_ai_hub.core.persistence.rag.datalake.entities.bucket_entity import BucketEntity
from swiss_ai_hub.core.persistence.rag.datalake.entities.namespace_entity import NamespaceEntity

pytestmark = pytest.mark.integration

_RUN = uuid.uuid4().hex[:8]
_DB = f"kdocindex{_RUN}"
_FINANCE = BucketNamespacePair(bucket_name=_DB, namespace_name="finance")
_LEGAL = BucketNamespacePair(bucket_name=_DB, namespace_name="legal")
_EXPRESSION = "documentdb_core.bson_get_value_text(document, '__data__.text')"
_TEXTS = {
    "acme": "Invoice\nSupplier: Zeta Dynamics AG\nRef ORDER-4711-XQ",
    "pruef": "Der Prüfbericht liegt vor.\r\nDie Äußerung des Kunden",
    "nfd": unicodedata.normalize("NFD", "Kopf\nNeuer Prüfbericht Q3"),
    "micro": "Dosis: 5 µg Wirkstoff pro Tablette",
    "mu": "Dosis: 5 μg Wirkstoff pro Kapsel",
    "path": 'Ablage C:\\Daten\\"Bericht" ist 100% sicher_v2',
    "edges": "Quartalsbericht am Anfang\nMitte\nund am Ende Quartalsbericht",
}


def _admin() -> psycopg.Connection:
    settings = KnowledgeTextIndexSettings()
    return psycopg.connect(
        host=settings.HOST,
        port=settings.PORT,
        dbname=settings.DATABASE,
        user=os.environ.get("MONGO_USERNAME", "admin"),
        password=os.environ.get("MONGO_PASSWORD", ""),
        autocommit=True,
        connect_timeout=3,
    )


def _collection_id(admin: psycopg.Connection) -> int:
    return admin.execute(
        "SELECT collection_id FROM documentdb_api_catalog.collections "
        "WHERE database_name = %s AND collection_name = 'documents-data'",
        (_DB,),
    ).fetchone()[0]


def _build_index(admin: psycopg.Connection) -> None:
    settings = KnowledgeTextIndexSettings()
    role, password = sql.Identifier(settings.USER), settings.PASSWORD.get_secret_value()
    collection_id = _collection_id(admin)
    admin.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    if admin.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (settings.USER,)).fetchone() is None:
        admin.execute(sql.SQL("CREATE ROLE {} LOGIN").format(role))
    admin.execute(sql.SQL("ALTER ROLE {} WITH LOGIN PASSWORD {}").format(role, sql.Literal(password)))
    admin.execute(
        sql.SQL(
            "GRANT USAGE ON SCHEMA documentdb_data, documentdb_core, documentdb_api_catalog, documentdb_api_internal "
            "TO {}"
        ).format(role)
    )
    admin.execute(sql.SQL("GRANT SELECT ON documentdb_api_catalog.collections TO {}").format(role))
    index = sql.Identifier(f"aihub_text_trgm_{collection_id}")
    table = sql.Identifier("documentdb_data", f"documents_{collection_id}")
    admin.execute(
        sql.SQL("CREATE INDEX IF NOT EXISTS {} ON {} USING gin (({}) gin_trgm_ops)").format(
            index, table, sql.SQL(_EXPRESSION)
        )
    )
    _stamp(admin, _current_stamp(admin))
    admin.execute(sql.SQL("GRANT SELECT ON {} TO {}").format(table, role))


def _current_stamp(admin: psycopg.Connection) -> str:
    version = admin.execute("SELECT extversion FROM pg_extension WHERE extname = 'documentdb_core'").fetchone()[0]
    return f"documentdb_core {version}"


def _stamp(admin: psycopg.Connection, stamp: str | None) -> None:
    index = sql.Identifier("documentdb_data", f"aihub_text_trgm_{_collection_id(admin)}")
    admin.execute(sql.SQL("COMMENT ON INDEX {} IS {}").format(index, sql.Literal(stamp)))


@pytest.fixture(autouse=True)
def indexed_database() -> Iterator[dict[str, str]]:
    if not KnowledgeTextIndexSettings().enabled:
        pytest.skip("KNOWLEDGE_TEXT_INDEX_PASSWORD is not set")
    try:
        admin = _admin()
    except psycopg.OperationalError as unreachable:
        pytest.skip(f"FerretDB's PostgreSQL is not reachable: {unreachable}")
    connect(
        db=AIHubSettings().MONGO_MAIN_DB_NAME,
        host=MongoSettings().CONNECTION_STRING.get_secret_value(),
        uuidRepresentation="standard",
    )
    bucket = BucketEntity.create_bucket(_DB)
    for name in ("finance", "legal"):
        NamespaceEntity.create_namespace(str(bucket.id), name, folder_name=name)
    MongoConnectionRegistry.ensure_alias(_DB)
    get_db(_DB).client.drop_database(_DB)

    ids = {key: _seed(_FINANCE, f"{key}.md", text) for key, text in _TEXTS.items()}
    ids["pending"] = _seed(_FINANCE, "pending.md", "Zeta Dynamics AG pending", is_ingested=False)
    ids["placeholder"] = _seed(_FINANCE, "new.md", "Zeta Dynamics AG", is_ingested=False, type_="placeholder")
    ids["msa"] = _seed(_LEGAL, "msa.md", "Master agreement with zeta dynamics ag")
    _build_index(admin)
    yield ids

    get_db(_DB).client.drop_database(_DB)
    NamespaceEntity.objects(bucket_id=str(bucket.id)).delete()
    bucket.delete()
    disconnect()
    admin.close()


def _seed(collection: BucketNamespacePair, path: str, text: str, **fields: bool | str | None) -> str:
    source = f"s3://{collection.bucket_name}/{collection.namespace_name}/{path}"
    return KnowledgeDocumentSeeder.insert(collection.bucket_name, collection.namespace_name, source, text, **fields)


async def _candidates(query: str, case_sensitive: bool = False) -> list[str] | None:
    index_query = KnowledgeTextIndexQuery.from_query(query, is_regex=False, case_sensitive=case_sensitive)
    assert index_query is not None
    return (await KnowledgeTextIndex.candidate_ids([_DB], index_query, 5.0))[_DB]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("query", "case_sensitive", "keys"),
    [
        ("Zeta Dynamics AG", False, {"acme"}),
        ("zeta dynamics ag", True, set()),
        ("Prüfbericht", False, {"pruef", "nfd"}),
        ("PRÜFBERICHT", False, {"pruef", "nfd"}),
        ("Äußerung des", False, {"pruef"}),
        ("5 μg Wirkstoff", False, {"micro", "mu"}),
        ("5 µg Wirkstoff", True, {"micro"}),
        ('C:\\Daten\\"Bericht"', False, {"path"}),
        ("100% sicher_v2", False, {"path"}),
        ("Quartalsbericht", False, {"edges"}),
        ("nirgends vorhanden", False, set()),
    ],
)
async def test_the_index_path_returns_exactly_what_the_scan_returns(
    monkeypatch: pytest.MonkeyPatch, indexed_database: dict[str, str], query: str, case_sensitive: bool, keys: set[str]
) -> None:
    """Pending, placeholder and other-namespace documents also contain the terms; the re-filter keeps them out."""
    assert await _candidates(query, case_sensitive) is not None

    indexed = await KnowledgeContentSearch.search([_FINANCE], query, case_sensitive=case_sensitive)
    monkeypatch.setenv("KNOWLEDGE_TEXT_INDEX_PASSWORD", "")
    scanned = await KnowledgeContentSearch.search([_FINANCE], query, case_sensitive=case_sensitive)

    assert {match.summary.id for match in indexed.matches} == {indexed_database[key] for key in keys}
    assert indexed.model_dump() == scanned.model_dump()


@pytest.mark.asyncio
@pytest.mark.parametrize("stamp", [None, "documentdb_core 0.0-0"])
async def test_an_index_not_checked_against_the_running_documentdb_is_ignored(stamp: str | None) -> None:
    with _admin() as admin:
        _stamp(admin, stamp)
        try:
            assert await _candidates("Zeta Dynamics AG") is None
        finally:
            _stamp(admin, _current_stamp(admin))
    assert await _candidates("Zeta Dynamics AG") is not None


@pytest.mark.asyncio
async def test_a_database_without_an_index_is_scanned(indexed_database: dict[str, str]) -> None:
    with _admin() as admin:
        admin.execute(
            sql.SQL("DROP INDEX documentdb_data.{}").format(sql.Identifier(f"aihub_text_trgm_{_collection_id(admin)}"))
        )
        assert await _candidates("Zeta Dynamics AG") is None
        result = await KnowledgeContentSearch.search([_FINANCE], "Zeta Dynamics AG")
        assert {match.summary.id for match in result.matches} == {indexed_database["acme"]}


@pytest.mark.asyncio
async def test_a_role_that_cannot_log_in_sends_the_search_to_the_scan(
    monkeypatch: pytest.MonkeyPatch, indexed_database: dict[str, str]
) -> None:
    monkeypatch.setenv("KNOWLEDGE_TEXT_INDEX_PASSWORD", "not-the-password")

    assert await _candidates("Zeta Dynamics AG") is None
    result = await KnowledgeContentSearch.search([_FINANCE], "Zeta Dynamics AG")
    assert {match.summary.id for match in result.matches} == {indexed_database["acme"]}


def test_the_read_only_role_cannot_write() -> None:
    settings = KnowledgeTextIndexSettings()
    with (
        psycopg.connect(
            host=settings.HOST,
            port=settings.PORT,
            dbname=settings.DATABASE,
            user=settings.USER,
            password=settings.PASSWORD.get_secret_value(),
            autocommit=True,
        ) as reader,
        _admin() as admin,
    ):
        table = sql.Identifier("documentdb_data", f"documents_{_collection_id(admin)}")
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            reader.execute(sql.SQL("DELETE FROM {}").format(table))
