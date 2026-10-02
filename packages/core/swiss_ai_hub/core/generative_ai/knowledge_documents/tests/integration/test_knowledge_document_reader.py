import asyncio
import time
import unicodedata
import uuid
from collections.abc import Iterator

import pytest
from mongoengine import connect, disconnect
from mongoengine.connection import get_db

from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_collection_not_found_error import (
    KnowledgeCollectionNotFoundError,
)
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_document_not_found_error import (
    KnowledgeDocumentNotFoundError,
)
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_document_pending_error import (
    KnowledgeDocumentPendingError,
)
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_document_reader import KnowledgeDocumentReader
from swiss_ai_hub.core.generative_ai.retrievers.bucket_namespace_pair import BucketNamespacePair
from swiss_ai_hub.core.infrastructure.api.ai_hub_settings import AIHubSettings
from swiss_ai_hub.core.infrastructure.mongo.mongo_connection_registry import MongoConnectionRegistry
from swiss_ai_hub.core.infrastructure.mongo.mongo_settings import MongoSettings
from swiss_ai_hub.core.persistence.rag.datalake.entities.bucket_entity import BucketEntity
from swiss_ai_hub.core.persistence.rag.datalake.entities.namespace_entity import NamespaceEntity
from swiss_ai_hub.core.persistence.rag.documents.entities.ref_doc import RefDoc
from swiss_ai_hub.core.persistence.rag.documents.utils.id_utils import source_to_doc_id

pytestmark = pytest.mark.integration

# Unique per run: the doc-store databases live outside the test database the session fixture drops, so fixed names
# would let an interrupted run's rows fail every later one on duplicate ids.
_RUN = uuid.uuid4().hex[:8]
_DB_A = f"kdocreader{_RUN}a"
_DB_B = f"kdocreader{_RUN}b"
_FINANCE = BucketNamespacePair(bucket_name=_DB_A, namespace_name="finance")
_LEGAL = BucketNamespacePair(bucket_name=_DB_A, namespace_name="legal")
_BULK = BucketNamespacePair(bucket_name=_DB_A, namespace_name="bulk")
_GONE = BucketNamespacePair(bucket_name=_DB_A, namespace_name="gone")
_HR = BucketNamespacePair(bucket_name=_DB_B, namespace_name="hr")
_NFD_PATH = unicodedata.normalize("NFD", "invoices/Prüfbericht-Ä.md")


def _insert(
    db_name: str,
    namespace: str,
    source: str,
    text: str = "parsed text",
    is_ingested: bool | None = True,
    type_: str = "4",
) -> str:
    doc_id = source_to_doc_id(source)
    metadata = {
        "source": source,
        "namespace": namespace,
        "version": "1",
        "created_at": 1735689600,
        "updated_at": 1735689600,
        "inserted_at": 1735689600,
        "content_hash": "hash",
        "type": "content",
        "document_title": None,
    }
    if is_ingested is not None:
        metadata["is_ingested"] = is_ingested
    get_db(db_name)["documents-data"].insert_one(
        {
            "_id": doc_id,
            "__type__": type_,
            "__data__": {
                "id_": doc_id,
                "text": text,
                "text_resource": {"text": text},
                "mimetype": "text/plain",
                "metadata": metadata,
            },
        }
    )
    return doc_id


@pytest.fixture(autouse=True)
def knowledge_databases() -> Iterator[dict[str, str]]:
    connect(
        db=AIHubSettings().MONGO_MAIN_DB_NAME,
        host=MongoSettings().CONNECTION_STRING.get_secret_value(),
        uuidRepresentation="standard",
    )
    bucket_a = BucketEntity.create_bucket(_DB_A)
    bucket_b = BucketEntity.create_bucket(_DB_B)
    NamespaceEntity.create_namespace(str(bucket_a.id), "finance", folder_name="Finanzen")
    NamespaceEntity.create_namespace(str(bucket_a.id), "legal", folder_name="legal")
    NamespaceEntity.create_namespace(str(bucket_a.id), "bulk", folder_name="bulk")
    gone = NamespaceEntity.create_namespace(str(bucket_a.id), "gone", folder_name="gone")
    NamespaceEntity.mark_deleting(str(gone.id))
    NamespaceEntity.create_namespace(str(bucket_b.id), "hr", folder_name="hr")
    for db_name in (_DB_A, _DB_B):
        MongoConnectionRegistry.ensure_alias(db_name)
        get_db(db_name).client.drop_database(db_name)

    ids = {
        "acme": _insert(_DB_A, "finance", f"s3://{_DB_A}/Finanzen/invoices/2025/q1/acme.pdf", text="ACME " * 1000),
        "legacy": _insert(_DB_A, "finance", f"s3://{_DB_A}/Finanzen/invoices/2024/legacy.pdf", is_ingested=None),
        "umlaut": _insert(_DB_A, "finance", f"s3://{_DB_A}/Finanzen/{_NFD_PATH}"),
        "pending": _insert(_DB_A, "finance", f"s3://{_DB_A}/Finanzen/invoices/2025/resync.pdf", is_ingested=False),
        "placeholder": _insert(
            _DB_A, "finance", f"s3://{_DB_A}/Finanzen/invoices/2025/new.pdf", is_ingested=False, type_="placeholder"
        ),
        "msa": _insert(_DB_A, "legal", f"s3://{_DB_A}/legal/contracts/msa.md"),
        "hr_acme": _insert(_DB_B, "hr", f"s3://{_DB_B}/hr/invoices/2025/q1/acme.pdf", text="HR copy"),
    }
    yield ids

    for db_name in (_DB_A, _DB_B):
        get_db(db_name).client.drop_database(db_name)
    for bucket in (bucket_a, bucket_b):
        NamespaceEntity.objects(bucket_id=str(bucket.id)).delete()
        bucket.delete()
    disconnect()


@pytest.mark.asyncio
async def test_lists_ingested_and_legacy_documents_but_not_pending_ones() -> None:
    listing = await KnowledgeDocumentReader.list_documents([_FINANCE, _LEGAL])

    assert [(doc.collection.namespace_name, doc.path) for doc in listing.documents] == [
        ("finance", "invoices/2024/legacy.pdf"),
        ("finance", "invoices/2025/q1/acme.pdf"),
        ("finance", _NFD_PATH),
        ("legal", "contracts/msa.md"),
    ]
    assert listing.total == 4
    assert listing.documents[1].filename == "acme.pdf"
    assert listing.documents[1].title == "acme.pdf"


def test_the_listing_query_loads_neither_copy_of_the_parsed_text() -> None:
    """llama-index writes the text twice; the e2e caught the listing still pulling the `text_resource` copy."""
    rows = RefDoc.list_ingested_summaries(_DB_A, "finance")

    assert len(rows) == 3
    assert all(row.data.text is None for row in rows)
    assert all(getattr(row.data, "text_resource", None) is None for row in rows)
    assert all(row.data.metadata.source and row.type_ == "4" for row in rows)


@pytest.mark.asyncio
async def test_lists_two_knowledge_databases_in_one_call(knowledge_databases: dict[str, str]) -> None:
    listing = await KnowledgeDocumentReader.list_documents([_HR, _LEGAL])

    assert {doc.id for doc in listing.documents} == {knowledge_databases["hr_acme"], knowledge_databases["msa"]}


@pytest.mark.asyncio
async def test_listing_filters_by_glob(knowledge_databases: dict[str, str]) -> None:
    listing = await KnowledgeDocumentReader.list_documents([_FINANCE, _HR])

    matched = listing.matching_glob("invoices/2025/**/*.pdf")

    assert {doc.id for doc in matched.documents} == {knowledge_databases["acme"], knowledge_databases["hr_acme"]}


@pytest.mark.asyncio
async def test_loads_the_complete_text_by_id(knowledge_databases: dict[str, str]) -> None:
    document = await KnowledgeDocumentReader.load_document([_FINANCE, _LEGAL], knowledge_databases["acme"])

    assert document.text == "ACME " * 1000
    assert document.text_length == 5000
    assert document.summary.path == "invoices/2025/q1/acme.pdf"


@pytest.mark.asyncio
async def test_loads_a_character_range(knowledge_databases: dict[str, str]) -> None:
    document = await KnowledgeDocumentReader.load_document([_FINANCE], knowledge_databases["acme"], start=5, end=14)

    assert document.text == "ACME ACME"
    assert (document.start, document.end, document.text_length) == (5, 14, 5000)


@pytest.mark.asyncio
@pytest.mark.parametrize(("key", "collections"), [("msa", [_FINANCE]), ("hr_acme", [_FINANCE, _LEGAL])])
async def test_rejects_an_id_from_a_collection_that_was_not_passed(
    knowledge_databases: dict[str, str], key: str, collections: list[BucketNamespacePair]
) -> None:
    with pytest.raises(KnowledgeDocumentNotFoundError, match="List the documents"):
        await KnowledgeDocumentReader.load_document(collections, knowledge_databases[key])


@pytest.mark.asyncio
async def test_rejects_an_unknown_id() -> None:
    with pytest.raises(KnowledgeDocumentNotFoundError):
        await KnowledgeDocumentReader.load_document([_FINANCE], "0123456789abcdef01234567")


@pytest.mark.asyncio
@pytest.mark.parametrize("key", ["pending", "placeholder"])
async def test_rejects_a_document_still_being_ingested(knowledge_databases: dict[str, str], key: str) -> None:
    with pytest.raises(KnowledgeDocumentPendingError, match="still being ingested"):
        await KnowledgeDocumentReader.load_document([_FINANCE], knowledge_databases[key])


@pytest.mark.asyncio
async def test_loads_by_path_within_the_named_collection(knowledge_databases: dict[str, str]) -> None:
    finance = await KnowledgeDocumentReader.load_document_by_path(
        [_FINANCE, _HR], _FINANCE, "invoices/2025/q1/acme.pdf"
    )
    hr = await KnowledgeDocumentReader.load_document_by_path([_FINANCE, _HR], _HR, "/invoices/2025/q1/acme.pdf")

    assert finance.summary.id == knowledge_databases["acme"]
    assert hr.summary.id == knowledge_databases["hr_acme"]
    assert hr.text == "HR copy"


@pytest.mark.asyncio
async def test_loads_by_composed_path_a_file_stored_decomposed(knowledge_databases: dict[str, str]) -> None:
    document = await KnowledgeDocumentReader.load_document_by_path(
        [_FINANCE], _FINANCE, unicodedata.normalize("NFC", _NFD_PATH)
    )

    assert document.summary.id == knowledge_databases["umlaut"]


@pytest.mark.asyncio
async def test_load_by_path_rejects_a_collection_that_was_not_passed() -> None:
    with pytest.raises(KnowledgeDocumentNotFoundError):
        await KnowledgeDocumentReader.load_document_by_path([_FINANCE], _HR, "invoices/2025/q1/acme.pdf")


@pytest.mark.asyncio
async def test_load_by_path_rejects_an_unknown_path() -> None:
    with pytest.raises(KnowledgeDocumentNotFoundError):
        await KnowledgeDocumentReader.load_document_by_path([_FINANCE], _FINANCE, "invoices/2025/q1/missing.pdf")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("collection", "reason"),
    [
        (BucketNamespacePair(bucket_name="kdocreadertestnope", namespace_name="finance"), "does not exist"),
        (BucketNamespacePair(bucket_name=_DB_A, namespace_name="nope"), "does not exist"),
        (_GONE, "is being deleted"),
    ],
)
async def test_an_unusable_collection_fails_the_whole_call(collection: BucketNamespacePair, reason: str) -> None:
    with pytest.raises(KnowledgeCollectionNotFoundError, match=reason):
        await KnowledgeDocumentReader.list_documents([_FINANCE, collection])


@pytest.mark.asyncio
async def test_concurrent_reads_of_two_databases_never_cross(knowledge_databases: dict[str, str]) -> None:
    """Worker threads used to share one `switch_db` binding of `RefDoc`: half of these calls got the other database."""
    finance_ids = {knowledge_databases[key] for key in ("acme", "legacy", "umlaut")}
    hr_ids = {knowledge_databases["hr_acme"]}

    for _ in range(50):
        finance, hr, hr_document = await asyncio.gather(
            KnowledgeDocumentReader.list_documents([_FINANCE]),
            KnowledgeDocumentReader.list_documents([_HR]),
            KnowledgeDocumentReader.load_document([_HR], knowledge_databases["hr_acme"]),
        )
        assert {doc.id for doc in finance.documents} == finance_ids
        assert {doc.id for doc in hr.documents} == hr_ids
        assert hr_document.text == "HR copy"


@pytest.mark.asyncio
async def test_load_by_path_ignores_a_sibling_collection_being_deleted(knowledge_databases: dict[str, str]) -> None:
    document = await KnowledgeDocumentReader.load_document_by_path(
        [_FINANCE, _GONE], _FINANCE, "invoices/2025/q1/acme.pdf"
    )

    assert document.summary.id == knowledge_databases["acme"]


@pytest.mark.asyncio
async def test_load_by_path_from_a_collection_being_deleted_fails() -> None:
    with pytest.raises(KnowledgeCollectionNotFoundError, match="is being deleted"):
        await KnowledgeDocumentReader.load_document_by_path([_FINANCE, _GONE], _GONE, "any.pdf")


@pytest.mark.asyncio
async def test_lists_a_few_hundred_documents_in_one_call() -> None:
    large_text = "x" * 100_000
    for index in range(300):
        _insert(_DB_A, "bulk", f"s3://{_DB_A}/bulk/batch-{index // 50:02d}/doc-{index:03d}.md", text=large_text)

    started = time.monotonic()
    listing = await KnowledgeDocumentReader.list_documents([_BULK])
    elapsed = time.monotonic() - started

    assert listing.total == 300
    assert listing.documents[0].path == "batch-00/doc-000.md"
    assert elapsed < 2
