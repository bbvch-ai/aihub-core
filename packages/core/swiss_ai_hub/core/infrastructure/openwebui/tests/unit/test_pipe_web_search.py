"""How the OpenWebUI pipe shows an agent's web search (#1568): the way OpenWebUI shows its own, with the queries while
it searches, then "Searched N sites" listing them, and every hit as a source the answer's citations number.

The pipe imports Open WebUI's own modules, which only exist inside that container, so they are stubbed to load it
from its file path.
"""

import importlib.util
import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from swiss_ai_hub.core.generative_ai import CitationId

pytestmark = pytest.mark.unit

REPO_ROOT = Path(__file__).resolve().parents[8]
TEMPLATE_PIPE = REPO_ROOT / "infra/deployment/templates/openwebui_functions/aihub_pipeline.py"
OPEN_WEBUI_MODULES = ["open_webui", "open_webui.models", "open_webui.models.chats", "open_webui.models.files"]
OPEN_WEBUI_MODULES += ["open_webui.models.users", "open_webui.utils", "open_webui.utils.chat_id"]

RELEASE = "https://example.com/release"
BLOG = "https://example.com/blog"


@pytest.fixture
def pipe(monkeypatch: pytest.MonkeyPatch) -> Any:
    for name in OPEN_WEBUI_MODULES:
        monkeypatch.setitem(sys.modules, name, MagicMock())
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
        agent_class="UniversalAgent",
        agent_id="assistant",
        thread_id="t1",
        stream_service=MagicMock(),
    )


async def _process(pipe: Any, event: dict[str, Any], context: Any) -> None:
    await pipe.EventProcessorFactory.create_chain().process(event, context)


def _node(url: str, title: str) -> dict[str, Any]:
    return {
        "id": url,
        "document_id": url,
        "content": f"What {title} says.",
        "source": url,
        "source_origin": url,
        "namespace": "web",
        "document_title": title,
        "citation_id": CitationId.of(url),
    }


def _searched(results: list[tuple[str, str]], queries: list[str] | None = None) -> dict[str, Any]:
    return {
        "_event_name": "WebSearchedEvent",
        "_parent_event_names": ["SemanticEvent", "DisplayEvent"],
        "queries": ["latest release"] if queries is None else queries,
        "results": [
            {"url": url, "title": title, "snippet": "", "engine": "brave", "read": False} for url, title in results
        ],
        "grounding_nodes": [_node(url, title) for url, title in results],
        "failures": [],
    }


class TestSearching:
    @pytest.mark.asyncio
    async def test_the_queries_show_while_the_agent_searches(self, pipe: Any) -> None:
        emitter = _Recorder()
        request = {"_event_name": "SearchWebEvent", "_parent_event_names": ["DisplayEvent"], "queries": ["release"]}

        await _process(pipe, request, _context(pipe, emitter))

        assert emitter.statuses == [{"action": "web_search_queries_generated", "queries": ["release"], "done": False}]

    @pytest.mark.asyncio
    async def test_a_profile_that_does_not_search_shows_no_progress(self, pipe: Any) -> None:
        emitter = _Recorder()
        request = {
            "_event_name": "SearchWebEvent",
            "_parent_event_names": ["DisplayEvent"],
            "queries": ["release"],
            "searching": False,
        }

        await _process(pipe, request, _context(pipe, emitter))

        assert emitter.events == []


class TestSearched:
    @pytest.mark.asyncio
    async def test_the_sites_searched_show_as_open_webuis_own_search_result(self, pipe: Any) -> None:
        emitter = _Recorder()

        await _process(pipe, _searched([(RELEASE, "Release"), (BLOG, "Blog")]), _context(pipe, emitter))

        assert emitter.statuses == [
            {
                "action": "web_search",
                "description": "Searched {{count}} sites",
                "items": [{"title": "Release", "link": RELEASE}, {"title": "Blog", "link": BLOG}],
                "done": True,
            }
        ]

    @pytest.mark.asyncio
    async def test_each_hit_is_a_source_with_its_title_and_url(self, pipe: Any) -> None:
        emitter = _Recorder()

        await _process(pipe, _searched([(RELEASE, "Release"), (BLOG, "Blog")]), _context(pipe, emitter))

        assert [(source["source"]["name"], source["source"]["url"]) for source in emitter.sources] == [
            ("Release", RELEASE),
            ("Blog", BLOG),
        ]

    @pytest.mark.asyncio
    async def test_a_cited_hit_becomes_the_number_of_its_source(self, pipe: Any) -> None:
        context = _context(pipe, _Recorder())
        await _process(pipe, _searched([(RELEASE, "Release"), (BLOG, "Blog")]), context)

        await _process(
            pipe,
            {"_parent_event_names": ["ChunkEvent"], "content": f"Version 2 is out [{CitationId.of(BLOG)}]."},
            context,
        )

        assert context.state_manager.serialize_to_html() == "Version 2 is out [2]."

    @pytest.mark.asyncio
    async def test_a_search_that_found_nothing_says_so(self, pipe: Any) -> None:
        emitter = _Recorder()

        await _process(pipe, _searched([]), _context(pipe, emitter))

        assert emitter.sources == []
        assert emitter.statuses == [
            {"action": "web_search", "description": "No search results found", "urls": [], "done": True}
        ]

    @pytest.mark.asyncio
    async def test_a_search_that_did_not_run_clears_the_status(self, pipe: Any) -> None:
        """With the profile or the toggle off the search answers empty, so its progress must not linger."""
        emitter = _Recorder()

        await _process(pipe, _searched([], queries=[]), _context(pipe, emitter))

        assert emitter.statuses == [{"action": None, "description": "", "done": True}]
