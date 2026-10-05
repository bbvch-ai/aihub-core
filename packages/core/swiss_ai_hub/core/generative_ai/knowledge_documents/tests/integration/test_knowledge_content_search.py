import asyncio
import time
import unicodedata
import uuid
from collections.abc import Iterator

import pytest
from mongoengine import connect, disconnect
from mongoengine.connection import get_db

from swiss_ai_hub.core.generative_ai.knowledge_documents.invalid_path_pattern_error import InvalidPathPatternError
from swiss_ai_hub.core.generative_ai.knowledge_documents.invalid_search_pattern_error import InvalidSearchPatternError
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_collection_not_found_error import (
    KnowledgeCollectionNotFoundError,
)
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_content_search import KnowledgeContentSearch
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_content_search_limits import (
    KnowledgeContentSearchLimits,
)
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_content_search_result import (
    KnowledgeContentSearchResult,
)
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_content_search_timeout_error import (
    KnowledgeContentSearchTimeoutError,
)
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_document_reader import KnowledgeDocumentReader
from swiss_ai_hub.core.generative_ai.knowledge_documents.tests.integration.knowledge_document_seeder import (
    KnowledgeDocumentSeeder,
)
from swiss_ai_hub.core.generative_ai.retrievers.bucket_namespace_pair import BucketNamespacePair
from swiss_ai_hub.core.infrastructure.api.ai_hub_settings import AIHubSettings
from swiss_ai_hub.core.infrastructure.mongo.mongo_connection_registry import MongoConnectionRegistry
from swiss_ai_hub.core.infrastructure.mongo.mongo_settings import MongoSettings
from swiss_ai_hub.core.persistence.rag.datalake.entities.bucket_entity import BucketEntity
from swiss_ai_hub.core.persistence.rag.datalake.entities.namespace_entity import NamespaceEntity
from swiss_ai_hub.core.persistence.rag.documents.entities.ref_doc import RefDoc

pytestmark = pytest.mark.integration

# Unique per run, as in the reader's tests: the doc-store databases outlive the test database the session drops.
_RUN = uuid.uuid4().hex[:8]
_DB_A = f"kdocsearch{_RUN}a"
_DB_B = f"kdocsearch{_RUN}b"
_FINANCE = BucketNamespacePair(bucket_name=_DB_A, namespace_name="finance")
_LEGAL = BucketNamespacePair(bucket_name=_DB_A, namespace_name="legal")
_BULK = BucketNamespacePair(bucket_name=_DB_A, namespace_name="bulk")
_GONE = BucketNamespacePair(bucket_name=_DB_A, namespace_name="gone")
_HR = BucketNamespacePair(bucket_name=_DB_B, namespace_name="hr")


def _source(collection: BucketNamespacePair, path: str) -> str:
    return f"s3://{collection.bucket_name}/{collection.namespace_name}/{path}"


def _seed(collection: BucketNamespacePair, path: str, text: str, **fields: bool | str | None) -> str:
    return KnowledgeDocumentSeeder.insert(
        collection.bucket_name, collection.namespace_name, _source(collection, path), text, **fields
    )


@pytest.fixture(autouse=True)
def knowledge_databases() -> Iterator[dict[str, str]]:
    connect(
        db=AIHubSettings().MONGO_MAIN_DB_NAME,
        host=MongoSettings().CONNECTION_STRING.get_secret_value(),
        uuidRepresentation="standard",
    )
    bucket_a = BucketEntity.create_bucket(_DB_A)
    bucket_b = BucketEntity.create_bucket(_DB_B)
    for name in ("finance", "legal", "bulk"):
        NamespaceEntity.create_namespace(str(bucket_a.id), name, folder_name=name)
    gone = NamespaceEntity.create_namespace(str(bucket_a.id), "gone", folder_name="gone")
    NamespaceEntity.mark_deleting(str(gone.id))
    NamespaceEntity.create_namespace(str(bucket_b.id), "hr", folder_name="hr")
    for db_name in (_DB_A, _DB_B):
        MongoConnectionRegistry.ensure_alias(db_name)
        get_db(db_name).client.drop_database(db_name)

    ids = {
        "acme": _seed(_FINANCE, "invoices/2025/acme.md", "Invoice\nSupplier: Zeta Dynamics AG\nRef ORDER-4711-XQ"),
        "rfc": _seed(_FINANCE, "specs/quic.md", "Intro\nSee RFC\n9000 and RFC 9000 again\nEnd"),
        "pruef": _seed(_FINANCE, "reports/pruef.md", "Der Prüfbericht liegt vor.\nDie Äußerung des Kunden"),
        "nfd": _seed(_FINANCE, "reports/nfd.md", unicodedata.normalize("NFD", "Kopf\nNeuer Prüfbericht Q3")),
        "plain_u": _seed(_FINANCE, "reports/plain.md", "Der Prufbericht ohne Umlaut"),
        "legacy": _seed(_FINANCE, "invoices/2024/legacy.md", "Zeta Dynamics AG, 2024", is_ingested=None),
        "pending": _seed(_FINANCE, "invoices/2025/pending.md", "Zeta Dynamics AG pending", is_ingested=False),
        "placeholder": _seed(
            _FINANCE, "invoices/2025/new.md", "Zeta Dynamics AG", is_ingested=False, type_="placeholder"
        ),
        "msa": _seed(_LEGAL, "contracts/msa.md", "Master agreement with zeta dynamics ag"),
        "hr": _seed(_HR, "invoices/2025/acme.md", "HR copy: Zeta Dynamics AG"),
    }
    yield ids

    for db_name in (_DB_A, _DB_B):
        get_db(db_name).client.drop_database(db_name)
    for bucket in (bucket_a, bucket_b):
        NamespaceEntity.objects(bucket_id=str(bucket.id)).delete()
        bucket.delete()
    disconnect()


def _ids(result: KnowledgeContentSearchResult) -> set[str]:
    return {match.summary.id for match in result.matches}


@pytest.mark.asyncio
async def test_finds_every_document_with_the_term_across_databases(knowledge_databases: dict[str, str]) -> None:
    result = await KnowledgeContentSearch.search([_FINANCE, _LEGAL, _HR], "Zeta Dynamics AG")

    assert _ids(result) == {knowledge_databases[key] for key in ("acme", "legacy", "msa", "hr")}
    assert (result.total_documents, result.next_offset, result.truncated) == (4, None, False)
    acme = next(match for match in result.matches if match.summary.id == knowledge_databases["acme"])
    assert acme.summary.path == "invoices/2025/acme.md"
    assert [(line.line_number, line.text) for line in acme.lines] == [(2, "Supplier: Zeta Dynamics AG")]


@pytest.mark.asyncio
async def test_line_offsets_read_back_the_same_text_through_the_reader(knowledge_databases: dict[str, str]) -> None:
    result = await KnowledgeContentSearch.search([_FINANCE], "prüfbericht")

    assert _ids(result) == {knowledge_databases["pruef"], knowledge_databases["nfd"]}
    for match in result.matches:
        line = match.lines[0]
        document = await KnowledgeDocumentReader.load_document([_FINANCE], match.summary.id, line.start, line.end)
        assert document.text == line.text
        assert "Prüfbericht" in unicodedata.normalize("NFC", line.text)


@pytest.mark.asyncio
async def test_searches_only_the_collections_passed(knowledge_databases: dict[str, str]) -> None:
    result = await KnowledgeContentSearch.search([_HR], "Zeta Dynamics AG")

    assert _ids(result) == {knowledge_databases["hr"]}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("query", "is_regex", "keys"),
    [
        (r"RFC\s+9000", True, {"rfc"}),
        (r"ORDER-\d{4}-[A-Z]{2}", True, {"acme"}),
        ("4711", False, {"acme"}),
        ("PRÜFBERICHT", False, {"pruef", "nfd"}),
        (r"\bÄußerung\b", True, {"pruef"}),
        (r"Pr\wfbericht", True, {"pruef", "plain_u"}),
    ],
)
async def test_regexes_substrings_and_umlauts_match_as_in_python(
    knowledge_databases: dict[str, str], query: str, is_regex: bool, keys: set[str]
) -> None:
    result = await KnowledgeContentSearch.search([_FINANCE], query, is_regex=is_regex)

    assert _ids(result) == {knowledge_databases[key] for key in keys}


@pytest.mark.asyncio
async def test_a_match_across_lines_is_reported_at_its_first_line(knowledge_databases: dict[str, str]) -> None:
    exact = await KnowledgeContentSearch.search([_FINANCE], "RFC 9000")
    spanning = await KnowledgeContentSearch.search([_FINANCE], r"RFC\s+9000", is_regex=True)

    assert [line.line_number for line in exact.matches[0].lines] == [3]
    assert [line.line_number for line in spanning.matches[0].lines] == [2, 3]


@pytest.mark.asyncio
async def test_case_sensitive_search_needs_the_same_case(knowledge_databases: dict[str, str]) -> None:
    result = await KnowledgeContentSearch.search([_FINANCE, _LEGAL], "zeta dynamics ag", case_sensitive=True)

    assert _ids(result) == {knowledge_databases["msa"]}


@pytest.mark.asyncio
async def test_a_database_match_without_a_python_match_is_dropped_from_page_and_total(
    knowledge_databases: dict[str, str],
) -> None:
    """The decomposed `[ü]` is a class holding `u`, so the database also matches `Prufbericht`; Python does not."""
    result = await KnowledgeContentSearch.search([_FINANCE], "Pr[ü]fbericht", is_regex=True)

    assert _ids(result) == {knowledge_databases["pruef"]}
    assert result.total_documents == 1


@pytest.mark.asyncio
async def test_a_path_glob_narrows_the_search(knowledge_databases: dict[str, str]) -> None:
    result = await KnowledgeContentSearch.search([_FINANCE, _HR], "Zeta Dynamics AG", path_glob="invoices/2025/**")

    assert _ids(result) == {knowledge_databases["acme"], knowledge_databases["hr"]}


@pytest.mark.asyncio
async def test_an_invalid_glob_fails_before_searching() -> None:
    with pytest.raises(InvalidPathPatternError, match="empty"):
        await KnowledgeContentSearch.search([_FINANCE], "Zeta", path_glob="/")


@pytest.mark.asyncio
async def test_pages_together_return_every_match_exactly_once() -> None:
    expected = {_seed(_BULK, f"page/doc-{index:02d}.md", f"line\nTreffer {index}") for index in range(30)}
    limits = KnowledgeContentSearchLimits(max_documents=10)

    seen: list[str] = []
    offset: int | None = 0
    pages = 0
    while offset is not None:
        result = await KnowledgeContentSearch.search([_BULK], "treffer", offset=offset, limits=limits)
        assert result.total_documents == 30
        seen.extend(match.summary.id for match in result.matches)
        offset, pages = result.next_offset, pages + 1

    assert pages == 3
    assert sorted(seen) == sorted(expected)


@pytest.mark.asyncio
async def test_lines_are_capped_but_all_counted() -> None:
    _seed(_BULK, "many.md", "\n".join(f"{index} Mahnung" for index in range(30)))
    limits = KnowledgeContentSearchLimits(max_lines_per_document=5)

    result = await KnowledgeContentSearch.search([_BULK], "mahnung", limits=limits)

    match = result.matches[0]
    assert (len(match.lines), match.matching_line_count, match.lines_truncated) == (5, 30, True)


def test_the_candidate_query_loads_neither_copy_of_the_text() -> None:
    rows = RefDoc.search_ingested_ids(_DB_A, "finance", "(*UCP)Zeta", "mi", 5000)

    assert len(rows) == 2
    assert all(row.data is None for row in rows)


def _seed_scale(count: int, planted_index: int | None = None) -> None:
    text = ("Lieferschein Gewährleistung Zahlungsfrist Rückerstattung " * 550)[:30000]
    rows = [
        KnowledgeDocumentSeeder.row("bulk", _source(_BULK, f"scale/doc-{index:04d}.md"), text) for index in range(count)
    ]
    if planted_index is not None:
        rows[planted_index]["__data__"]["text"] += "\nAuftrag ORDER-0777-ZZ"
    get_db(_DB_A)["documents-data"].insert_many(rows)


@pytest.mark.asyncio
async def test_a_scan_longer_than_the_budget_is_cancelled_in_the_database() -> None:
    _seed_scale(2000)
    limits = KnowledgeContentSearchLimits(timeout_seconds=0.05)
    started = time.monotonic()

    with pytest.raises(KnowledgeContentSearchTimeoutError, match="narrow it"):
        await KnowledgeContentSearch.search([_BULK], "quuxplorer", limits=limits)

    assert time.monotonic() - started < 1


@pytest.mark.asyncio
async def test_a_pattern_only_python_accepts_is_rejected_with_a_hint() -> None:
    with pytest.raises(InvalidSearchPatternError, match="PCRE2"):
        await KnowledgeContentSearch.search([_FINANCE], r"(?<=\d+)X", is_regex=True)


@pytest.mark.asyncio
async def test_changes_are_found_at_once() -> None:
    document_id = _seed(_BULK, "live.md", "first quuxplorer draft")
    assert _ids(await KnowledgeContentSearch.search([_BULK], "quuxplorer")) == {document_id}

    get_db(_DB_A)["documents-data"].update_one(
        {"_id": document_id}, {"$set": {"__data__.text": "second wobblefrog draft"}}
    )
    assert _ids(await KnowledgeContentSearch.search([_BULK], "quuxplorer")) == set()
    assert _ids(await KnowledgeContentSearch.search([_BULK], "wobblefrog")) == {document_id}

    get_db(_DB_A)["documents-data"].delete_one({"_id": document_id})
    assert _ids(await KnowledgeContentSearch.search([_BULK], "wobblefrog")) == set()


@pytest.mark.asyncio
async def test_a_collection_being_deleted_fails_the_whole_call() -> None:
    with pytest.raises(KnowledgeCollectionNotFoundError, match="is being deleted"):
        await KnowledgeContentSearch.search([_FINANCE, _GONE], "Zeta")


@pytest.mark.asyncio
async def test_a_negative_offset_is_rejected() -> None:
    with pytest.raises(ValueError, match="offset"):
        await KnowledgeContentSearch.search([_FINANCE], "Zeta", offset=-1)


@pytest.mark.asyncio
async def test_concurrent_searches_of_two_databases_never_cross(knowledge_databases: dict[str, str]) -> None:
    for _ in range(20):
        finance, hr = await asyncio.gather(
            KnowledgeContentSearch.search([_FINANCE], "Zeta Dynamics AG"),
            KnowledgeContentSearch.search([_HR], "Zeta Dynamics AG"),
        )
        assert _ids(finance) == {knowledge_databases["acme"], knowledge_databases["legacy"]}
        assert _ids(hr) == {knowledge_databases["hr"]}


@pytest.mark.asyncio
async def test_searches_a_thousand_long_documents_in_one_call() -> None:
    _seed_scale(1000, planted_index=777)
    started = time.monotonic()

    result = await KnowledgeContentSearch.search([_BULK], "ORDER-0777-ZZ")

    assert time.monotonic() - started < 2
    assert [match.summary.path for match in result.matches] == ["scale/doc-0777.md"]
