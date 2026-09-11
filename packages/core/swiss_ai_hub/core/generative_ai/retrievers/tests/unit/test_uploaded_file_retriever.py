"""The uploaded-file retriever reads what the chat client already indexed.

Open WebUI parses every upload through this platform's parsing API, embeds it with the configured model
and writes one Milvus collection per file. These tests pin the two things that make reading those
collections safe: the name is derived from the client's file id exactly the way Open WebUI derives it,
and a file whose collection does not exist yet degrades to no nodes instead of ending the turn — a user
can always ask before the upload finished indexing.
"""

from unittest.mock import MagicMock, patch

import pytest

from swiss_ai_hub.core.events.agent.user.user_uploaded_file import UserUploadedFile
from swiss_ai_hub.core.generative_ai.resources.models.llm.embedding_model_config import EmbeddingModelConfig
from swiss_ai_hub.core.generative_ai.retrievers.uploaded_file_retriever import UploadedFileRetriever
from swiss_ai_hub.core.generative_ai.retrievers.uploaded_file_retriever_config import UploadedFileRetrieverConfig
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler

_FILE_ID = "bfdc8835-a20d-43f5-8f21-ff8140ad83d3"
_COLLECTION = "open_webui_file_bfdc8835_a20d_43f5_8f21_ff8140ad83d3"


def _config() -> UploadedFileRetrieverConfig:
    return UploadedFileRetrieverConfig(embed_model=EmbeddingModelConfig(model_name="embedding/bge-m3"), retrieve_k=16)


def _file(source_file_id: str | None = _FILE_ID, filename: str = "handbook.pdf") -> UserUploadedFile:
    return UserUploadedFile(
        filename=filename,
        file_type="application/pdf",
        file_id=_FILE_ID,
        source_file_id=source_file_id,
    )


def _hit(text: str, distance: float = 0.83, metadata: dict | None = None) -> dict:
    return {
        "id": "chunk-1",
        "distance": distance,
        "entity": {"data": {"text": text}, "metadata": metadata or {}},
    }


def _client(hits: list[dict], has_collection: bool = True) -> MagicMock:
    client = MagicMock()
    client.has_collection.return_value = has_collection
    client.search.return_value = [hits]
    return client


def _patched(client: MagicMock):
    return (
        patch("swiss_ai_hub.core.generative_ai.retrievers.uploaded_file_retriever.MilvusClient", return_value=client),
        patch.object(UploadedFileRetriever, "_embed_query", return_value=[0.1] * 8),
    )


def test_collection_name_matches_open_webui_sanitisation():
    """Open WebUI prefixes ``open_webui`` and replaces every dash, so the ids must line up exactly."""
    assert UploadedFileRetriever.collection_name_for(_FILE_ID) == _COLLECTION


def test_files_without_a_client_index_are_dropped():
    """A file forwarded by a client that never indexed it has no collection to read."""
    retriever = UploadedFileRetriever(_config(), [_file(source_file_id=None)])

    assert retriever.files == []


@pytest.mark.asyncio
async def test_no_files_does_not_touch_milvus():
    retriever = UploadedFileRetriever(_config(), [])

    with patch(
        "swiss_ai_hub.core.generative_ai.retrievers.uploaded_file_retriever.MilvusClient"
    ) as milvus_client_class:
        nodes = await retriever.retrieve("anything", LocaleHandler())

    assert nodes == []
    milvus_client_class.assert_not_called()


@pytest.mark.asyncio
async def test_missing_collection_degrades_to_no_nodes():
    """Asking right after an upload is normal; the collection may not exist yet and must not end the turn."""
    client = _client(hits=[], has_collection=False)
    retriever = UploadedFileRetriever(_config(), [_file()])

    milvus_patch, embed_patch = _patched(client)
    with milvus_patch, embed_patch:
        nodes = await retriever.retrieve("what is the policy?", LocaleHandler())

    assert nodes == []
    client.search.assert_not_called()


@pytest.mark.asyncio
async def test_hits_become_nodes_attributed_to_the_uploaded_file():
    client = _client(hits=[_hit("Employees get 25 days.")])
    retriever = UploadedFileRetriever(_config(), [_file()])

    milvus_patch, embed_patch = _patched(client)
    with milvus_patch, embed_patch:
        nodes = await retriever.retrieve("how many vacation days?", LocaleHandler())

    assert len(nodes) == 1
    node = nodes[0]
    assert node.content == "Employees get 25 days."
    assert node.source == "handbook.pdf"
    assert node.document_title == "handbook.pdf"
    assert node.document_id == _FILE_ID
    assert node.namespace == _FILE_ID
    assert node.source_origin == UploadedFileRetriever.SOURCE_ORIGIN_NAME
    assert node.score == 0.83


@pytest.mark.asyncio
async def test_the_searched_collection_is_the_one_the_client_indexed():
    client = _client(hits=[_hit("chunk")])
    retriever = UploadedFileRetriever(_config(), [_file()])

    milvus_patch, embed_patch = _patched(client)
    with milvus_patch, embed_patch:
        await retriever.retrieve("q", LocaleHandler())

    assert client.search.call_args.kwargs["collection_name"] == _COLLECTION
    assert client.search.call_args.kwargs["anns_field"] == UploadedFileRetriever.VECTOR_FIELD
    assert client.search.call_args.kwargs["limit"] == 16


@pytest.mark.asyncio
async def test_every_attached_file_is_searched():
    """Twenty attachments must all be reachable — one collection per file, searched in parallel."""
    client = _client(hits=[_hit("chunk")])
    files = [_file(filename=f"doc-{index}.pdf") for index in range(20)]
    retriever = UploadedFileRetriever(_config(), files)

    milvus_patch, embed_patch = _patched(client)
    with milvus_patch, embed_patch:
        nodes = await retriever.retrieve("q", LocaleHandler())

    assert client.search.call_count == 20
    assert len(nodes) == 20
