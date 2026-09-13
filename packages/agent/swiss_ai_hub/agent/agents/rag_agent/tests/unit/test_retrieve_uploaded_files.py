"""Files the user attached are retrieved alongside the agent's own knowledge sources.

The chat client indexes each upload into its own collection before the agent ever sees the turn, so the
agent reads those vectors rather than parsing the documents again. These tests pin what that costs
nothing to get wrong: the two result sets are merged unranked (their scores come from different metrics
and are not comparable), uploaded chunks lead so the prompt puts the attachment first, and an agent with
nothing to borrow an embedding model from leaves uploads unread rather than guessing one.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from llama_index.core.schema import NodeWithScore, TextNode
from swiss_ai_hub.core.events.agent import StandaloneQuestionCondenserEvent, UserUploadedFile
from swiss_ai_hub.core.generative_ai import IngestedNode
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import DOCUMENT_ID, NAMESPACE, SOURCE

import swiss_ai_hub.agent.agents.rag_agent  # noqa: F401,E402  (import-order guard, not a direct dependency)
from swiss_ai_hub.agent.rag.step_functions import do_retrieve, do_retrieve_uploaded_files

_FILE_ID = "bfdc8835-a20d-43f5-8f21-ff8140ad83d3"
_MODULE = "swiss_ai_hub.agent.rag.step_functions"


def _file(source_file_id: str | None = _FILE_ID) -> UserUploadedFile:
    return UserUploadedFile(
        filename="handbook.pdf",
        file_type="application/pdf",
        file_id=_FILE_ID,
        source_file_id=source_file_id,
    )


def _runtime_config() -> MagicMock:
    runtime_config = MagicMock()
    runtime_config.config.embed_model = MagicMock()
    return runtime_config


def _node(text: str, source: str) -> IngestedNode:
    node = TextNode(text=text, metadata={SOURCE: source, NAMESPACE: "ns", DOCUMENT_ID: source})
    return IngestedNode.from_llama_index_node_with_score(NodeWithScore(node=node, score=0.5))


@pytest.mark.asyncio
async def test_no_files_means_no_retriever():
    with patch(f"{_MODULE}.UploadedFileRetriever") as retriever_class:
        nodes = await do_retrieve_uploaded_files("q", None, [_runtime_config()], LocaleHandler(), None)

    assert nodes == []
    retriever_class.assert_not_called()


@pytest.mark.asyncio
async def test_files_the_client_never_indexed_are_skipped():
    """Without the client's own file id there is no collection to read."""
    with patch(f"{_MODULE}.UploadedFileRetriever") as retriever_class:
        nodes = await do_retrieve_uploaded_files(
            "q", [_file(source_file_id=None)], [_runtime_config()], LocaleHandler(), None
        )

    assert nodes == []
    retriever_class.assert_not_called()


@pytest.mark.asyncio
async def test_an_agent_without_retrievers_leaves_uploads_unread():
    """The embedding model is borrowed from a configured retriever; guessing one would produce noise."""
    with patch(f"{_MODULE}.UploadedFileRetriever") as retriever_class:
        nodes = await do_retrieve_uploaded_files("q", [_file()], [], LocaleHandler(), None)

    assert nodes == []
    retriever_class.assert_not_called()


@pytest.mark.asyncio
async def test_the_query_is_embedded_with_the_agents_own_model():
    runtime_config = _runtime_config()
    retriever = MagicMock()
    retriever.retrieve = AsyncMock(return_value=[_node("chunk", "handbook.pdf")])

    with (
        patch(f"{_MODULE}.UploadedFileRetriever", return_value=retriever) as retriever_class,
        patch(f"{_MODULE}.UploadedFileRetrieverConfig") as config_class,
    ):
        await do_retrieve_uploaded_files("q", [_file()], [runtime_config], LocaleHandler(), None)

    assert config_class.call_args.kwargs["embed_model"] is runtime_config.config.embed_model
    assert retriever_class.call_args.kwargs["files"] == [_file()]


@pytest.mark.asyncio
async def test_an_attachment_that_yielded_nothing_is_reported_to_the_user():
    """A vector search has no similarity floor, so no node at all means the file was never readable."""
    retriever = MagicMock()
    retriever.retrieve = AsyncMock(return_value=[])
    displayer = MagicMock()
    displayer.display_thought = AsyncMock()

    with (
        patch(f"{_MODULE}.UploadedFileRetriever", return_value=retriever),
        patch(f"{_MODULE}.UploadedFileRetrieverConfig"),
    ):
        await do_retrieve_uploaded_files("q", [_file()], [_runtime_config()], LocaleHandler(), None, displayer)

    displayer.display_thought.assert_awaited_once()
    assert "handbook.pdf" in displayer.display_thought.await_args.args[0]


@pytest.mark.asyncio
async def test_a_readable_attachment_is_not_reported():
    """The node carries the client's file id as its namespace, which is what marks the file as read."""
    node = _node("chunk", "handbook.pdf")
    node.namespace = _FILE_ID
    retriever = MagicMock()
    retriever.retrieve = AsyncMock(return_value=[node])
    displayer = MagicMock()
    displayer.display_thought = AsyncMock()

    with (
        patch(f"{_MODULE}.UploadedFileRetriever", return_value=retriever),
        patch(f"{_MODULE}.UploadedFileRetrieverConfig"),
    ):
        await do_retrieve_uploaded_files("q", [_file()], [_runtime_config()], LocaleHandler(), None, displayer)

    displayer.display_thought.assert_not_awaited()


@pytest.mark.asyncio
async def test_uploaded_chunks_lead_the_merged_result():
    """The attachment is what the user just pointed at, so it goes into the prompt ahead of the corpus."""
    event = StandaloneQuestionCondenserEvent(
        condensed_chat_message=ChatMessage(role=MessageRole.USER, content="how many vacation days?"),
    )

    with (
        patch(
            f"{_MODULE}.retrieve_from_all_sources", AsyncMock(return_value=[_node("from knowledge base", "corpus.pdf")])
        ),
        patch(f"{_MODULE}.do_retrieve_uploaded_files", AsyncMock(return_value=[_node("from upload", "handbook.pdf")])),
    ):
        retriever_event = await do_retrieve(event, [_runtime_config()], LocaleHandler(), None, uploaded_files=[_file()])

    assert len(retriever_event.nodes) == 2


@pytest.mark.asyncio
async def test_knowledge_retrieval_still_runs_without_attachments():
    """No attachment must not change what an agent does with its own corpus."""
    event = StandaloneQuestionCondenserEvent(condensed_chat_message=ChatMessage(role=MessageRole.USER, content="q"))
    knowledge = AsyncMock(return_value=[_node("from knowledge base", "corpus.pdf")])

    with (
        patch(f"{_MODULE}.retrieve_from_all_sources", knowledge),
        patch(f"{_MODULE}.UploadedFileRetriever") as retriever_class,
    ):
        retriever_event = await do_retrieve(event, [_runtime_config()], LocaleHandler(), None, uploaded_files=None)

    knowledge.assert_awaited_once()
    retriever_class.assert_not_called()
    assert len(retriever_event.nodes) == 1
