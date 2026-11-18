"""Unit tests for how the OpenWebUI pipe turns the ids agents cite into the numbers Open WebUI links.

Open WebUI resolves ``[n]`` to the n-th distinct source of the message, so the pipe numbers every source it emits
and rewrites ``[s…]`` markers to those numbers. The pipe imports Open WebUI's own modules, which only exist inside
that container, so they are stubbed to load it from its file path.
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
GENERATED_PIPE = REPO_ROOT / "infra/configs/openwebui/functions/aihub_pipeline.py"
OPEN_WEBUI_MODULES = ["open_webui", "open_webui.models", "open_webui.models.chats", "open_webui.models.files"]
OPEN_WEBUI_MODULES += ["open_webui.models.users"]
OPEN_WEBUI_MODULES += ["open_webui.utils", "open_webui.utils.chat_id"]


def _is_saved_chat_id(chat_id: str | None) -> bool:
    """Open WebUI 0.11.3's own rule, since a stubbed one would call every chat saved."""
    return bool(chat_id) and not chat_id.startswith(("temporary:", "local:", "channel:"))


HANDBOOK = CitationId.of("handbook.pdf")
POLICY = CitationId.of("policy.pdf")


@pytest.fixture
def pipe(monkeypatch: pytest.MonkeyPatch) -> Any:
    for name in OPEN_WEBUI_MODULES:
        monkeypatch.setitem(sys.modules, name, MagicMock())
    sys.modules["open_webui.utils.chat_id"].is_saved_chat_id = _is_saved_chat_id
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
        file_id = CitationId.of("agent-file")
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


class TestReferencedKnowledge:
    """A `#` reference to one of our collections reaches the agent as a reference, never as a file, and what the agent
    found there is listed as sources like a knowledge agent's own retrieval."""

    @pytest.mark.asyncio
    async def test_what_a_referenced_collection_returned_is_listed_as_sources(self, pipe: Any) -> None:
        emitter = _Recorder()
        event = {**_grounding(_node("handbook.pdf", "25 days")), "_event_name": "KnowledgeSearchedEvent"}

        await pipe.EventProcessorFactory.create_chain().process(event, _context(pipe, emitter))

        assert [source["document"] for source in emitter.sources] == [["25 days"]]

    @pytest.mark.asyncio
    async def test_a_referenced_collection_is_not_uploaded_as_a_file(self, pipe: Any) -> None:
        service = pipe.FileProcessingService.__new__(pipe.FileProcessingService)

        files, owui_file_ids = await service.prepare_files_for_event(
            [{"type": "collection", "id": "k1", "name": "HR / Policies"}], "RAGAgent", "hr", {}, "t1", "user-1"
        )

        assert (files, owui_file_ids) == ([], {})
        pipe.Files.get_file_by_id.assert_not_called()

    @pytest.mark.asyncio
    async def test_only_referenced_collections_are_resolved_once_each(
        self, pipe: Any, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        response = MagicMock(json=MagicMock(return_value=[{"database": "hr", "namespace": "policies"}]))
        client = MagicMock(post=AsyncMock(return_value=response))
        client.__aenter__ = AsyncMock(return_value=client)
        client.__aexit__ = AsyncMock(return_value=None)
        monkeypatch.setattr(pipe.httpx, "AsyncClient", MagicMock(return_value=client))
        files = [{"type": "collection", "id": "k1"}, {"type": "file", "id": "f1"}, {"type": "collection", "id": "k1"}]

        references = await pipe.KnowledgeReferenceService("http://api").references_for_event(files, {"X": "y"})

        assert references == [{"database": "hr", "namespace": "policies"}]
        url = client.post.await_args.args[0]
        assert url == "http://api/api/v1/active/knowledge/openwebui-references"
        assert client.post.await_args.kwargs["json"] == {"openwebui_ids": ["k1"]}

    @pytest.mark.asyncio
    async def test_a_message_without_references_asks_nothing(self, pipe: Any, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(pipe.httpx, "AsyncClient", MagicMock(side_effect=AssertionError("no request expected")))

        assert await pipe.KnowledgeReferenceService("http://api").references_for_event([{"type": "file"}], {}) == []


def test_generated_copy_matches_template() -> None:
    assert GENERATED_PIPE.read_text() == TEMPLATE_PIPE.read_text()


TENANT = "tenant-1"
THREAD = "0123456789abcdef01234567"
DOCUMENT = "s3://manuals/devices/Nr 196 1.pdf"
FIGURE = "s3://manuals/devices/__figures__/Nr_196_1_pdf/figure_0a1b2c3d4e5f6a7b.jpg"


def _figure(reference: str = FIGURE, source: str = DOCUMENT) -> dict[str, Any]:
    return {**_node(source, f"![Figure 1]({reference})"), "content_type": "figure", "document_title": "Nr 196 1"}


def _figure_context(pipe: Any, emitter: _Recorder) -> Any:
    context = _context(pipe, emitter)
    context.thread_id = THREAD
    context.stream_service = MagicMock(active_tenant_id=AsyncMock(return_value=TENANT))
    return context


async def _documents(pipe: Any, *nodes: dict[str, Any]) -> tuple[list[str], Any]:
    emitter = _Recorder()
    context = _figure_context(pipe, emitter)
    await pipe.EventProcessorFactory.create_chain().process(_grounding(*nodes), context)
    return [document for source in emitter.sources for document in source["document"]], context


class TestFigures:
    @pytest.mark.asyncio
    async def test_a_figure_is_linked_through_the_figure_route_on_open_webui(self, pipe: Any) -> None:
        documents, _ = await _documents(pipe, _figure())

        assert documents == [
            f"![Figure 1](/hub-figures/{TENANT}/{THREAD}/manuals/devices/__figures__/Nr_196_1_pdf/"
            "figure_0a1b2c3d4e5f6a7b.jpg)"
        ]

    @pytest.mark.asyncio
    async def test_each_path_segment_is_percent_encoded(self, pipe: Any) -> None:
        source = "s3://manuals/Geräte X/a b.pdf"
        reference = "s3://manuals/Geräte X/__figures__/a_b_pdf/figure_1.png"

        documents, _ = await _documents(pipe, _figure(reference, source))

        assert "/manuals/Ger%C3%A4te%20X/__figures__/a_b_pdf/figure_1.png)" in documents[0]

    @pytest.mark.asyncio
    async def test_the_tenant_is_asked_for_once_per_answer(self, pipe: Any) -> None:
        _, context = await _documents(pipe, _figure(), _figure(source="s3://manuals/other.pdf"))

        context.stream_service.active_tenant_id.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_text_only_sources_never_ask_for_the_tenant(self, pipe: Any) -> None:
        _, context = await _documents(pipe, _node("handbook.pdf", "25 days"))

        context.stream_service.active_tenant_id.assert_not_awaited()

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "reference",
        [
            "s3://other-tenant/folder/__figures__/x_pdf/figure_1.png",
            "s3://manuals/devices/__figures__/Nr_196_1_pdf/figure_1.svg",
        ],
    )
    async def test_a_figure_the_route_would_refuse_becomes_a_caption(self, pipe: Any, reference: str) -> None:
        documents, _ = await _documents(pipe, _figure(reference))

        assert documents == ["*Figure 1 (Nr 196 1)*"]

    @pytest.mark.asyncio
    async def test_a_reference_in_a_text_chunk_is_left_as_written(self, pipe: Any) -> None:
        documents, _ = await _documents(pipe, _node("notes.pdf", f"see ![x]({FIGURE})"))

        assert documents == [f"see ![x]({FIGURE})"]


@pytest.mark.parametrize("source", ["s3://manuals/devices/Nr 196 1.pdf", "s3://b/a/x.y#z?.docx", "s3://b/plain"])
def test_the_figure_folder_matches_the_one_ingestion_writes(pipe: Any, source: str) -> None:
    from swiss_ai_hub.core.generative_ai import create_figures_folder_name

    assert pipe.FigureLinks.figures_folder(source) == create_figures_folder_name(source)
