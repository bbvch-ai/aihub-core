"""Unit tests for how the OpenWebUI pipe turns the ids agents cite into the numbers Open WebUI links.

Open WebUI resolves ``[n]`` to the n-th distinct source of the message, so the pipe numbers every source it emits
and rewrites ``[s…]`` markers to those numbers. The pipe imports Open WebUI's own modules, which only exist inside
that container, so they are stubbed to load it from its file path.
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
GENERATED_PIPE = REPO_ROOT / "infra/configs/openwebui/functions/aihub_pipeline.py"
OPEN_WEBUI_MODULES = ["open_webui", "open_webui.models", "open_webui.models.chats", "open_webui.models.files"]
OPEN_WEBUI_MODULES += ["open_webui.models.users"]

HANDBOOK = CitationId.of("handbook.pdf")
POLICY = CitationId.of("policy.pdf")


@pytest.fixture
def pipe(monkeypatch: pytest.MonkeyPatch) -> Any:
    for name in OPEN_WEBUI_MODULES:
        monkeypatch.setitem(sys.modules, name, MagicMock())
    spec = importlib.util.spec_from_file_location("aihub_pipeline", TEMPLATE_PIPE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _node(source: str, content: str) -> dict[str, Any]:
    return {
        "source": source,
        "citation_id": CitationId.of(source),
        "content": content,
        "document_title": source.removesuffix(".pdf").title(),
        "document_id": f"doc-{source}",
    }


class _Recorder:
    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    async def __call__(self, event: dict[str, Any]) -> None:
        self.events.append(event)

    @property
    def sources(self) -> list[dict[str, Any]]:
        return [event["data"] for event in self.events if event["type"] == "source"]


def _context(pipe: Any, emitter: _Recorder, owui_file_ids: dict[str, str] | None = None) -> Any:
    return pipe.EventContext(
        state_manager=pipe.StreamingStateManager(),
        emitter=emitter,
        caller=MagicMock(),
        headers={},
        agent_class="RAGAgent",
        agent_id="hr",
        thread_id="t1",
        stream_service=MagicMock(),
        owui_file_ids=owui_file_ids,
    )


async def _answer(pipe: Any, context: Any, text: str) -> str:
    await pipe.EventProcessorFactory.create_chain().process(
        {"_parent_event_names": ["ChunkEvent"], "content": text}, context
    )
    return context.state_manager.serialize_to_html()


def _grounding(*nodes: dict[str, Any]) -> dict[str, Any]:
    return {"_event_name": "InOrderNodeCombinerEvent", "_parent_event_names": [], "grounding_nodes": list(nodes)}


class TestKnowledgeSources:
    @pytest.mark.asyncio
    async def test_one_source_per_document_with_every_chunk(self, pipe: Any) -> None:
        emitter = _Recorder()
        context = _context(pipe, emitter)

        await pipe.EventProcessorFactory.create_chain().process(
            _grounding(_node("handbook.pdf", "25 days"), _node("policy.pdf", "remote"), _node("handbook.pdf", "carry")),
            context,
        )

        assert [source["document"] for source in emitter.sources] == [["25 days", "carry"], ["remote"]]
        assert {meta["name"] for meta in emitter.sources[0]["metadata"]} == {"Handbook"}

    @pytest.mark.asyncio
    async def test_the_chip_shows_the_file_name_not_the_storage_url(self, pipe: Any) -> None:
        emitter = _Recorder()
        node = {**_node("s3://knowledge/hr/handbook.pdf", "25 days"), "document_title": ""}

        await pipe.EventProcessorFactory.create_chain().process(_grounding(node), _context(pipe, emitter))

        assert emitter.sources[0]["metadata"][0]["name"] == "handbook.pdf"
        assert emitter.sources[0]["source"]["name"] == "handbook.pdf"

    @pytest.mark.asyncio
    async def test_cited_ids_become_the_numbers_of_their_sources(self, pipe: Any) -> None:
        context = _context(pipe, _Recorder())
        await pipe.EventProcessorFactory.create_chain().process(
            _grounding(_node("handbook.pdf", "25 days"), _node("policy.pdf", "remote")), context
        )

        answer = await _answer(
            pipe, context, f"Vacation is 25 days [{HANDBOOK}], remote work too [{POLICY}, {HANDBOOK}]."
        )

        assert answer == "Vacation is 25 days [1], remote work too [2][1]."

    @pytest.mark.asyncio
    async def test_an_id_never_emitted_is_dropped(self, pipe: Any) -> None:
        context = _context(pipe, _Recorder())

        assert await _answer(pipe, context, f"Made up [{HANDBOOK}].") == "Made up."

    @pytest.mark.asyncio
    async def test_a_marker_still_streaming_is_held_back(self, pipe: Any) -> None:
        context = _context(pipe, _Recorder())

        assert await _answer(pipe, context, f"Vacation is 25 days [{HANDBOOK[:4]}") == "Vacation is 25 days "

    @pytest.mark.asyncio
    async def test_memories_take_their_place_in_the_numbering(self, pipe: Any) -> None:
        context = _context(pipe, _Recorder())
        chain = pipe.EventProcessorFactory.create_chain()
        memory = {"_parent_event_names": ["RetrieveUserMemoryEvent"], "memories": [{"id": "m1", "memory": "Likes tea"}]}

        await chain.process(memory, context)
        await chain.process(_grounding(_node("handbook.pdf", "25 days")), context)

        assert await _answer(pipe, context, f"See [{HANDBOOK}].") == "See [2]."


class TestAttachedFileSources:
    @pytest.mark.asyncio
    async def test_an_attached_file_is_cited_by_its_own_id(self, pipe: Any) -> None:
        emitter = _Recorder()
        context = _context(pipe, emitter, owui_file_ids={"agent-file": "owui-file"})
        citation_id = CitationId.of("agent-file")
        event = {
            "_parent_event_names": ["AttachedFileEvent"],
            "file_id": "agent-file",
            "filename": "contract.pdf",
            "status": "read",
            "citation_id": citation_id,
            "content": "The text the model read.",
        }

        await pipe.EventProcessorFactory.create_chain().process(event, context)

        assert emitter.sources[0]["document"] == ["The text the model read."]
        assert emitter.sources[0]["metadata"][0]["file_id"] == "owui-file"
        assert await _answer(pipe, context, f"Signed [{citation_id}].") == "Signed [1]."


class TestSameNamedSources:
    @pytest.mark.asyncio
    async def test_a_file_and_a_document_sharing_a_name_get_their_own_numbers(self, pipe: Any) -> None:
        emitter = _Recorder()
        context = _context(pipe, emitter, owui_file_ids={"agent-file": "owui-file"})
        chain = pipe.EventProcessorFactory.create_chain()
        file_id = CitationId.for_attached_file("agent-file")
        document = {**_node("s3://knowledge/legal/contract.pdf", "Clause 7"), "document_title": "contract.pdf"}
        attached = {
            "_parent_event_names": ["AttachedFileEvent"],
            "file_id": "agent-file",
            "filename": "contract.pdf",
            "status": "read",
            "citation_id": file_id,
            "content": "Signed copy",
        }

        await chain.process(_grounding(document), context)
        await chain.process(attached, context)

        assert [source["metadata"][0]["name"] for source in emitter.sources] == ["contract.pdf", "contract.pdf (2)"]
        answer = await _answer(pipe, context, f"Clause 7 [{document['citation_id']}], signed [{file_id}].")
        assert answer == "Clause 7 [1], signed [2]."


def test_generated_copy_matches_template() -> None:
    assert GENERATED_PIPE.read_text() == TEMPLATE_PIPE.read_text()
