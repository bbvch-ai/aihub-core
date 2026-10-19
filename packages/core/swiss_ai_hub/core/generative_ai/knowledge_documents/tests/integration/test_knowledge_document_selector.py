import uuid
from collections.abc import Iterator

import pytest
from mongoengine import connect, disconnect
from mongoengine.connection import get_db

from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_document_criteria import KnowledgeDocumentCriteria
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_document_selection import (
    KnowledgeDocumentSelection,
)
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_document_selection_result import (
    KnowledgeDocumentSelectionResult,
)
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_document_selector import KnowledgeDocumentSelector
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
_DB = f"kdocselect{_RUN}"
_FINANCE = BucketNamespacePair(bucket_name=_DB, namespace_name="finance")
_LEGAL = BucketNamespacePair(bucket_name=_DB, namespace_name="legal")
_BOTH = [_FINANCE, _LEGAL]


def _seed(collection: BucketNamespacePair, path: str, text: str) -> str:
    source = f"s3://{collection.bucket_name}/{collection.namespace_name}/{path}"
    return KnowledgeDocumentSeeder.insert(collection.bucket_name, collection.namespace_name, source, text)


@pytest.fixture(autouse=True)
def documents() -> Iterator[dict[str, str]]:
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
    ids = {
        "acme_2025": _seed(_FINANCE, "invoices/2025/acme-1.md", "Supplier: Acme AG\nServer rack 1200 CHF"),
        "acme_body": _seed(_FINANCE, "invoices/2025/inv-77.md", "Supplier: Acme AG\nLaptop 900 CHF"),
        "globex_2025": _seed(_FINANCE, "invoices/2025/globex-1.md", "Supplier: Globex\nConsulting 300 CHF"),
        "acme_2024": _seed(_FINANCE, "invoices/2024/acme-0.md", "Supplier: Acme AG\nMonitor 200 CHF"),
        "contract": _seed(_LEGAL, "contracts/acme.md", "Framework agreement with Acme AG"),
    }
    yield ids
    get_db(_DB).client.drop_database(_DB)
    NamespaceEntity.objects(bucket_id=str(bucket.id)).delete()
    bucket.delete()
    disconnect()


def _ids(result: KnowledgeDocumentSelectionResult) -> set[str]:
    return {document.id for document in result.documents}


def _selection(*criteria: KnowledgeDocumentCriteria) -> KnowledgeDocumentSelection:
    return KnowledgeDocumentSelection(any_of=list(criteria))


@pytest.mark.asyncio
async def test_a_selection_matches_documents_meeting_any_of_its_criteria(documents: dict[str, str]) -> None:
    selection = _selection(
        KnowledgeDocumentCriteria(path_glob="invoices/2025/acme*"),
        KnowledgeDocumentCriteria(path_glob="invoices/2025/**", content_query="Acme AG"),
    )

    result = await KnowledgeDocumentSelector.resolve(_BOTH, selection, limit=10)

    assert _ids(result) == {documents["acme_2025"], documents["acme_body"]}
    assert result.truncated is False


@pytest.mark.asyncio
async def test_the_restricting_glob_holds_whatever_the_selection_asks_for(documents: dict[str, str]) -> None:
    selection = _selection(
        KnowledgeDocumentCriteria(path_glob="**", content_query="Acme AG"),
        KnowledgeDocumentCriteria(document_ids=[documents["contract"]]),
    )

    result = await KnowledgeDocumentSelector.resolve(_BOTH, selection, limit=10, restricting_glob="invoices/**")

    assert _ids(result) == {documents["acme_2025"], documents["acme_body"], documents["acme_2024"]}


@pytest.mark.asyncio
async def test_criteria_within_one_entry_must_all_hold(documents: dict[str, str]) -> None:
    selection = _selection(
        KnowledgeDocumentCriteria(path_regex=r"20(24|25)", content_query="monitor|laptop", content_is_regex=True)
    )

    result = await KnowledgeDocumentSelector.resolve(_BOTH, selection, limit=10)

    assert _ids(result) == {documents["acme_body"], documents["acme_2024"]}


@pytest.mark.asyncio
async def test_a_selection_beyond_the_limit_is_cut_and_says_so(documents: dict[str, str]) -> None:
    result = await KnowledgeDocumentSelector.resolve(
        _BOTH, _selection(KnowledgeDocumentCriteria(path_glob="invoices/**")), limit=2
    )

    assert [document.path for document in result.documents] == ["invoices/2024/acme-0.md", "invoices/2025/acme-1.md"]
    assert result.truncated is True


@pytest.mark.asyncio
async def test_a_document_selected_twice_is_returned_once(documents: dict[str, str]) -> None:
    selection = _selection(
        KnowledgeDocumentCriteria(document_ids=[documents["globex_2025"]]),
        KnowledgeDocumentCriteria(content_query="Globex"),
    )

    result = await KnowledgeDocumentSelector.resolve(_BOTH, selection, limit=10)

    assert [document.id for document in result.documents] == [documents["globex_2025"]]
