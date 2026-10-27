"""How the OpenWebUI pipe takes part in web fetch (#1569): a page referenced with `#` reaches the agent as its URL,
never as a file and never as Open WebUI's own copy of its text, and the pages the agent read come back as sources
with their title and URL, the links it could not read as a status.

The pipe imports Open WebUI's own modules, which only exist inside that container, so they are stubbed to load it
from its file path.
"""

import importlib.util
import sys
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from swiss_ai_hub.core.generative_ai import CitationId

pytestmark = pytest.mark.unit

REPO_ROOT = Path(__file__).resolve().parents[8]
TEMPLATE_PIPE = REPO_ROOT / "infra/deployment/templates/openwebui_functions/aihub_pipeline.py"
OPEN_WEBUI_MODULES = ["open_webui", "open_webui.models", "open_webui.models.chats", "open_webui.models.files"]
OPEN_WEBUI_MODULES += ["open_webui.models.users", "open_webui.utils", "open_webui.utils.chat_id"]

ARTICLE = "https://example.com/article"
PRICING = "https://example.com/pricing"


def _web_item(url: str) -> dict[str, Any]:
    """What Open WebUI 0.11.3 sends for a page attached with `#` (Attach Webpage): its text nested, no top-level id."""
    return {
        "type": "text",
        "name": url,
        "url": url,
        "collection_name": "web-abc",
        "status": "uploaded",
        "context": "full",
        "file": {"data": {"content": "The page as Open WebUI read it."}, "meta": {"name": url, "source": url}},
    }


TEMPORARY_TEXT = {"type": "text", "id": "browser-1", "name": "notes", "content": "A temporary chat's upload."}
UPLOADED_FILE = {"type": "file", "id": "owui-file-1", "url": "owui-file-1", "name": "report.pdf"}
COLLECTION = {"type": "collection", "id": "owui-knowledge-1"}


def _is_saved_chat_id(chat_id: str | None) -> bool:
    """Open WebUI 0.11.3's own rule, since a stubbed one would call every chat saved."""
    return bool(chat_id) and not chat_id.startswith(("temporary:", "local:", "channel:"))


@pytest.fixture
def pipe(monkeypatch: pytest.MonkeyPatch) -> Any:
    for name in OPEN_WEBUI_MODULES:
        monkeypatch.setitem(sys.modules, name, MagicMock())
    sys.modules["open_webui.utils.chat_id"].is_saved_chat_id = _is_saved_chat_id
    spec = importlib.util.spec_from_file_location("aihub_pipeline", TEMPLATE_PIPE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _Recorder:
    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    async def __call__(self, event: dict[str, Any]) -> None:
        self.events.append(event)

    @property
    def sources(self) -> list[dict[str, Any]]:
        return [event["data"] for event in self.events if event["type"] == "source"]

    @property
    def statuses(self) -> list[dict[str, Any]]:
        return [event["data"] for event in self.events if event["type"] == "status"]


def _context(pipe: Any, emitter: _Recorder) -> Any:
    return pipe.EventContext(
        state_manager=pipe.StreamingStateManager(),
        emitter=emitter,
        caller=MagicMock(),
        headers={},
        agent_class="RAGAgent",
        agent_id="hr",
        thread_id="t1",
        stream_service=MagicMock(),
    )


def _page(url: str, title: str) -> dict[str, Any]:
    """A page as `WebPagesFetchedEvent.grounding_nodes` carries it."""
    page_id = f"page-{url}"
    return {
        "id": page_id,
        "document_id": page_id,
        "citation_id": CitationId.of(page_id),
        "source": url,
        "source_origin": url,
        "namespace": "web",
        "document_title": title,
        "content": f"# {title}\n\nThe page's text.",
    }


def _fetched(pages: list[dict[str, Any]], failures: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {
        "_event_name": "WebPagesFetchedEvent",
        "_parent_event_names": ["SemanticEvent", "ControlAndDisplayEvent", "DisplayEvent"],
        "grounding_nodes": pages,
        "failures": failures or [],
    }


async def _process(pipe: Any, event: dict[str, Any], context: Any) -> None:
    await pipe.EventProcessorFactory.create_chain().process(event, context)


class TestWebReferences:
    def test_a_hash_referenced_page_is_forwarded_as_its_url_once(self, pipe: Any) -> None:
        files = [_web_item(ARTICLE), TEMPORARY_TEXT, UPLOADED_FILE, COLLECTION, _web_item(PRICING), _web_item(ARTICLE)]

        assert pipe.WebReferenceService.references_for_event(files) == [ARTICLE, PRICING]

    def test_a_message_without_files_references_no_page(self, pipe: Any) -> None:
        assert pipe.WebReferenceService.references_for_event(None) == []

    @pytest.mark.parametrize(
        "item", [TEMPORARY_TEXT, UPLOADED_FILE, COLLECTION], ids=["temporary", "file", "collection"]
    )
    def test_only_a_web_item_is_a_web_reference(self, pipe: Any, item: dict[str, Any]) -> None:
        assert not pipe.WebReferenceService.is_web_reference(item)

    @pytest.mark.asyncio
    async def test_a_referenced_page_is_never_uploaded_as_a_file(self, pipe: Any) -> None:
        """Open WebUI's copy of the text is dropped; the agent reads the page itself, through our browser."""
        pipe.Files.get_file_by_id = AsyncMock()
        service = pipe.FileProcessingService("http://api", "http://s3", "key", "secret")
        scope = pipe.TemporaryUploadScope(user_id="user-1", thread_id="t1")

        attachments = await service._resolve_all([_web_item(ARTICLE)], "RAGAgent/hr", scope)

        assert attachments == []
        pipe.Files.get_file_by_id.assert_not_awaited()


class TestFetchStatus:
    @pytest.mark.asyncio
    async def test_reading_linked_pages_shows_as_a_status(self, pipe: Any) -> None:
        emitter = _Recorder()
        request = {
            "_event_name": "FetchWebPagesEvent",
            "_parent_event_names": ["ControlAndDisplayEvent", "DisplayEvent"],
            "urls": [ARTICLE],
            "display_description": {"en": "Reading the linked web pages"},
        }

        await _process(pipe, request, _context(pipe, emitter))

        assert emitter.statuses == [{"action": None, "description": "Reading the linked web pages", "done": False}]

    @pytest.mark.asyncio
    async def test_a_turn_that_links_nothing_stays_silent(self, pipe: Any) -> None:
        """A web-fetching agent asks on every turn, so the request alone must not claim it is reading anything."""
        emitter = _Recorder()
        request = {"_event_name": "FetchWebPagesEvent", "_parent_event_names": ["DisplayEvent"], "urls": []}

        await _process(pipe, request, _context(pipe, emitter))

        assert emitter.events == []

    @pytest.mark.asyncio
    async def test_links_a_profile_does_not_read_show_no_progress(self, pipe: Any) -> None:
        """With web fetch off the links are left unread, so claiming to read them would mislead."""
        emitter = _Recorder()
        request = {
            "_event_name": "FetchWebPagesEvent",
            "_parent_event_names": ["DisplayEvent"],
            "urls": [ARTICLE],
            "reading": False,
            "display_description": {"en": "Reading the linked web pages"},
        }

        await _process(pipe, request, _context(pipe, emitter))

        assert emitter.events == []


class TestFetchedPages:
    @pytest.mark.asyncio
    async def test_each_page_read_is_a_source_with_its_title_and_url(self, pipe: Any) -> None:
        emitter = _Recorder()

        await _process(pipe, _fetched([_page(ARTICLE, "Article"), _page(PRICING, "Pricing")]), _context(pipe, emitter))

        assert [(source["source"]["name"], source["source"]["url"]) for source in emitter.sources] == [
            ("Article", ARTICLE),
            ("Pricing", PRICING),
        ]
        assert emitter.statuses == [{"action": None, "description": "Read 2 web pages", "done": True}]

    @pytest.mark.asyncio
    async def test_a_cited_page_becomes_the_number_of_its_source(self, pipe: Any) -> None:
        context = _context(pipe, _Recorder())
        article = _page(ARTICLE, "Article")
        await _process(pipe, _fetched([article]), context)

        await _process(
            pipe,
            {"_parent_event_names": ["ChunkEvent"], "content": f"Plans start at 10 CHF [{article['citation_id']}]."},
            context,
        )

        assert context.state_manager.serialize_to_html() == "Plans start at 10 CHF [1]."

    @pytest.mark.asyncio
    async def test_the_links_not_read_are_named_in_an_error_status(self, pipe: Any) -> None:
        emitter = _Recorder()
        failures = [{"url": "https://example.com/gone", "reason": "not_found"}]

        await _process(pipe, _fetched([], failures), _context(pipe, emitter))

        assert emitter.sources == []
        assert emitter.statuses == [
            {"description": "Could not read: https://example.com/gone", "done": True, "error": True}
        ]

    @pytest.mark.asyncio
    async def test_nothing_read_clears_the_reading_status(self, pipe: Any) -> None:
        """Fetching off for the profile answers empty, so the status the request showed must not linger."""
        emitter = _Recorder()

        await _process(pipe, _fetched([]), _context(pipe, emitter))

        assert emitter.statuses == [{"action": None, "description": "", "done": True}]
