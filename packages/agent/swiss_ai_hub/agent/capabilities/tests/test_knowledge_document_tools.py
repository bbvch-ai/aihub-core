"""The document tools list, search and read whole knowledge documents, only when the profile switches them on, and
never outside the collections of the run and the profile's glob, whatever the model asks for."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from swiss_ai_hub.core.agents import AgentConfig
from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.generative_ai import (
    BucketNamespacePair,
    KnowledgeContentLine,
    KnowledgeContentMatch,
    KnowledgeContentSearchResult,
    KnowledgeDocument,
    KnowledgeDocumentListing,
    KnowledgeDocumentNotFoundError,
    KnowledgeDocumentPendingError,
    KnowledgeDocumentSummary,
)
from swiss_ai_hub.core.i18n import LocaleString

from swiss_ai_hub.agent.capabilities.knowledge_documents.knowledge_document_collection import (
    KnowledgeDocumentCollection,
)
from swiss_ai_hub.agent.capabilities.knowledge_documents.knowledge_document_config import KnowledgeDocumentConfig
from swiss_ai_hub.agent.capabilities.knowledge_documents.knowledge_document_fields import KnowledgeDocumentFields
from swiss_ai_hub.agent.capabilities.knowledge_documents.knowledge_document_run_scope import (
    KnowledgeDocumentRunScope,
)
from swiss_ai_hub.agent.capabilities.knowledge_documents.knowledge_document_tools import (
    LISTING_PAGE_SIZE,
    READ_CHARACTERS,
    KnowledgeDocumentTools,
)
from swiss_ai_hub.agent.capabilities.tool_loop.tool_context import ToolContext
from swiss_ai_hub.agent.i18n.agent_locale_handler import AgentLocaleHandler

TOOLS = "swiss_ai_hub.agent.capabilities.knowledge_documents.knowledge_document_tools"
SCOPE = f"{TOOLS}.KnowledgeDocumentScope.for_tool"
FINANCE = BucketNamespacePair(bucket_name="finance-db", namespace_name="invoices")


class DocumentToolsConfig(KnowledgeDocumentFields, AgentConfig):
    pass


def _config(enabled: bool = True) -> DocumentToolsConfig:
    return DocumentToolsConfig(
        agent_id="documents",
        name=LocaleString(en="Documents"),
        description=LocaleString(en="Documents fixture"),
        knowledge_documents=KnowledgeDocumentConfig(enabled=enabled),
    )


def _tools(config: AgentConfig | None = None) -> KnowledgeDocumentTools:
    context = ToolContext(
        agent_config=config or _config(), displayer=MagicMock(spec=EventDisplayer), t=AgentLocaleHandler("en")
    )
    return KnowledgeDocumentTools(context)


def _scope(restricting_glob: str | None = "invoices/**") -> KnowledgeDocumentRunScope:
    return KnowledgeDocumentRunScope(
        collections=[KnowledgeDocumentCollection(identifier="finance/invoices", collection=FINANCE, label="Finance")],
        restricting_glob=restricting_glob,
    )


def _summary(path: str, document_id: str | None = None) -> KnowledgeDocumentSummary:
    return KnowledgeDocumentSummary(
        id=document_id or path.replace("/", "-"),
        collection=FINANCE,
        path=path,
        filename=path.rsplit("/", 1)[-1],
        title=path,
        file_type="pdf",
        updated_at=datetime(2025, 1, 1, tzinfo=UTC),
    )


def _listing(*paths: str) -> KnowledgeDocumentListing:
    return KnowledgeDocumentListing.from_summaries([_summary(path) for path in paths])


def test_disabled_tools_are_not_offered():
    assert _tools(_config(enabled=False)).to_tool_list() == []


def test_a_config_without_the_document_settings_offers_no_tools():
    config = AgentConfig(agent_id="plain", name=LocaleString(en="Plain"), description=LocaleString(en="Plain"))

    assert _tools(config).to_tool_list() == []


def test_enabled_tools_are_all_offered():
    names = {tool.metadata.name for tool in _tools().to_tool_list()}

    assert names == {"list_knowledge_documents", "search_knowledge_content", "read_knowledge_document"}


@pytest.mark.asyncio
async def test_a_listing_never_leaves_the_profiles_glob_whatever_the_model_asks_for():
    listing = _listing("invoices/2025/acme.pdf", "contracts/acme.pdf", "invoices/2024/globex.pdf")
    with (
        patch(SCOPE, AsyncMock(return_value=_scope())),
        patch(f"{TOOLS}.KnowledgeDocumentReader.list_documents", AsyncMock(return_value=listing)),
    ):
        text = await _tools().list_knowledge_documents(path_glob="**", path_regex="acme")

    assert "invoices/2025/acme.pdf" in text
    assert "contracts/" not in text
    assert text.startswith("Documents 1-1 of 1.")


@pytest.mark.asyncio
async def test_a_long_listing_comes_in_pages_that_say_where_to_continue():
    listing = _listing(*(f"invoices/2025/inv-{index:03d}.pdf" for index in range(LISTING_PAGE_SIZE + 5)))
    with (
        patch(SCOPE, AsyncMock(return_value=_scope())),
        patch(f"{TOOLS}.KnowledgeDocumentReader.list_documents", AsyncMock(return_value=listing)),
    ):
        first = await _tools().list_knowledge_documents(path_glob="**")
        second = await _tools().list_knowledge_documents(path_glob="**", offset=LISTING_PAGE_SIZE)

    assert first.startswith(f"Documents 1-{LISTING_PAGE_SIZE} of {LISTING_PAGE_SIZE + 5}; more with offset=60.")
    assert second.startswith(f"Documents 61-{LISTING_PAGE_SIZE + 5} of {LISTING_PAGE_SIZE + 5}.")
    assert len(first) / 4 < 3000


@pytest.mark.asyncio
async def test_an_empty_listing_shows_what_paths_look_like():
    with (
        patch(SCOPE, AsyncMock(return_value=_scope())),
        patch(
            f"{TOOLS}.KnowledgeDocumentReader.list_documents",
            AsyncMock(return_value=_listing("invoices/2025/acme-0001.pdf", "contracts/secret.pdf")),
        ),
    ):
        text = await _tools().list_knowledge_documents(path_glob="Acme*2025")

    assert text.startswith("No document path matches.")
    assert "'invoices/2025/acme-0001.pdf'" in text
    assert "contracts/secret.pdf" not in text


@pytest.mark.asyncio
async def test_a_content_search_applies_the_profiles_glob_next_to_the_models():
    match = KnowledgeContentMatch(
        summary=_summary("invoices/2025/acme.pdf"),
        lines=[KnowledgeContentLine(line_number=3, start=40, end=60, text="Server rack 1200 CHF", clipped=False)],
        matching_line_count=1,
    )
    search = AsyncMock(return_value=KnowledgeContentSearchResult(matches=[match], total_documents=1, next_offset=None))
    with patch(SCOPE, AsyncMock(return_value=_scope())), patch(f"{TOOLS}.KnowledgeContentSearch.search", search):
        text = await _tools().search_knowledge_content(query="rack", path_glob="**/*.pdf")

    assert search.await_args.kwargs["path_globs"] == ["invoices/**", "**/*.pdf"]
    assert "line 3 at 40: Server rack 1200 CHF" in text


@pytest.mark.asyncio
async def test_a_search_without_matches_suggests_other_queries():
    search = AsyncMock(return_value=KnowledgeContentSearchResult(matches=[], total_documents=0, next_offset=None))
    with patch(SCOPE, AsyncMock(return_value=_scope())), patch(f"{TOOLS}.KnowledgeContentSearch.search", search):
        text = await _tools().search_knowledge_content(query="Umbrella Corp")

    assert text.startswith("No document contains this.")


def _document(path: str, start: int, text_length: int) -> KnowledgeDocument:
    end = min(start + READ_CHARACTERS, text_length)
    return KnowledgeDocument(
        summary=_summary(path, "doc-1"), text="x" * (end - start), text_length=text_length, start=start, end=end
    )


@pytest.mark.asyncio
async def test_reading_returns_one_part_and_says_where_to_continue():
    load = AsyncMock(return_value=_document("invoices/2025/acme.pdf", 0, 30_000))
    with patch(SCOPE, AsyncMock(return_value=_scope())), patch(f"{TOOLS}.KnowledgeDocumentReader.load_document", load):
        text = await _tools().read_knowledge_document(document_id="doc-1")

    assert load.await_args.args[1:] == ("doc-1", 0, READ_CHARACTERS)
    assert f"characters 0-{READ_CHARACTERS} of 30000. More with start={READ_CHARACTERS}." in text


@pytest.mark.asyncio
async def test_reading_a_document_outside_the_profiles_glob_is_refused():
    load = AsyncMock(return_value=_document("contracts/acme.pdf", 0, 100))
    with patch(SCOPE, AsyncMock(return_value=_scope())), patch(f"{TOOLS}.KnowledgeDocumentReader.load_document", load):
        tools = _tools()
        with pytest.raises(LookupError, match="No access"):
            await tools.read_knowledge_document(document_id="doc-1")


@pytest.mark.asyncio
async def test_reading_a_document_of_another_collection_is_refused_as_no_access():
    load = AsyncMock(side_effect=KnowledgeDocumentNotFoundError("doc-9", [FINANCE]))
    with patch(SCOPE, AsyncMock(return_value=_scope())), patch(f"{TOOLS}.KnowledgeDocumentReader.load_document", load):
        tools = _tools()
        with pytest.raises(LookupError, match="No access to a document with id doc-9"):
            await tools.read_knowledge_document(document_id="doc-9")


@pytest.mark.asyncio
async def test_reading_a_pending_document_says_it_is_still_being_ingested():
    load = AsyncMock(side_effect=KnowledgeDocumentPendingError("doc-1", FINANCE))
    with patch(SCOPE, AsyncMock(return_value=_scope())), patch(f"{TOOLS}.KnowledgeDocumentReader.load_document", load):
        tools = _tools()
        with pytest.raises(LookupError, match="still being ingested"):
            await tools.read_knowledge_document(document_id="doc-1")


def _scope_config(narrow: bool) -> DocumentToolsConfig:
    from swiss_ai_hub.core.persistence import MilvusVectorStoreConfig

    from swiss_ai_hub.agent.capabilities.knowledge.knowledge_tool_config import KnowledgeToolConfig
    from swiss_ai_hub.agent.capabilities.knowledge.knowledge_tool_source import KnowledgeToolSource

    store = MilvusVectorStoreConfig(collection_name="finance", index_namespaces=["invoices"])
    return _config().model_copy(
        update={
            "knowledge_tool": KnowledgeToolConfig(sources=[KnowledgeToolSource(vector_store=store)]),
            "knowledge_documents": KnowledgeDocumentConfig(enabled=True, narrow_references=narrow, path_glob="**"),
        }
    )


@pytest.mark.parametrize(
    ("narrow", "expected"), [(True, ["finance/invoices"]), (False, ["finance/invoices", "hr/policies"])]
)
def test_a_reference_adds_a_collection_unless_the_profile_narrows(narrow: bool, expected: list[str]):
    from swiss_ai_hub.core.events.agent import KnowledgeReference

    from swiss_ai_hub.agent.capabilities.knowledge_documents.knowledge_document_scope import KnowledgeDocumentScope

    live = {"finance": ["invoices"], "hr": ["policies"]}
    reference = KnowledgeReference(database="hr", namespace="policies")
    with (
        patch(
            "swiss_ai_hub.agent.capabilities.knowledge.knowledge_tool_scope.UserScopedRetrievers.namespaces_of",
            side_effect=lambda database: live.get(database, []),
        ),
        patch(
            "swiss_ai_hub.agent.capabilities.knowledge_documents.knowledge_document_scope.KnowledgeCollectionResolver.pair_of",
            side_effect=lambda ref: BucketNamespacePair(bucket_name=ref.database, namespace_name=ref.namespace),
        ),
        patch(
            "swiss_ai_hub.agent.capabilities.knowledge_documents.knowledge_document_scope.KnowledgeCollectionLabel.of_reference",
            return_value="label",
        ),
    ):
        scope = KnowledgeDocumentScope.of(_scope_config(narrow), [reference], None, "en")

    assert [entry.identifier for entry in scope.collections] == expected
    assert scope.ignored == ([reference] if narrow else [])
