"""Rewriting a stored document's metadata in a real Milvus, as the classification backfill does (#2483).

One collection for the module: creating one takes its 1023 partitions, and rewriting is idempotent, so the tests
may share it in any order.
"""

import json
import uuid
from collections.abc import Iterator

import pytest
from llama_index.core.schema import NodeRelationship, RelatedNodeInfo, TextNode
from llama_index.core.vector_stores.utils import metadata_dict_to_node
from pymilvus import MilvusClient

from swiss_ai_hub.core.infrastructure.milvus.milvus_settings import MilvusSettings
from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import HASH, NAMESPACE, NODE_TYPE_CONTENT, TYPE
from swiss_ai_hub.core.persistence.rag.vectors.stores.milvus_vector_store_factory import create_milvus_vector_store
from swiss_ai_hub.core.persistence.rag.vectors.stores.partition_aware_milvus_vector_store import (
    PartitionAwareMilvusVectorStore,
)

pytestmark = pytest.mark.integration

_NAMESPACE = "finance"
_DIMENSION = 4
_CLASSIFICATION = {"document_type": "invoice", "document_issuer": "Hooli AG", "document_date": None}


def _node(node_id: str, document_id: str, embedding: list[float], content_hash: str = "hash-1") -> TextNode:
    return TextNode(
        id_=node_id,
        text=f"Chunk {node_id}",
        embedding=embedding,
        metadata={NAMESPACE: _NAMESPACE, TYPE: NODE_TYPE_CONTENT, HASH: content_hash, "project": "ABC"},
        excluded_embed_metadata_keys=["project"],
        relationships={NodeRelationship.SOURCE: RelatedNodeInfo(node_id=document_id)},
    )


@pytest.fixture(scope="module")
def vector_store() -> Iterator[PartitionAwareMilvusVectorStore]:
    settings = MilvusSettings()
    client = MilvusClient(uri=settings.URL, token=settings.get_token())
    collection_name = f"rewrite_metadata_{uuid.uuid4().hex[:8]}"
    store = create_milvus_vector_store(
        client=client,
        collection_name=collection_name,
        embedding_vector_dimension=_DIMENSION,
        uri=settings.URL,
        token=settings.get_token(),
    )
    store.add(
        [
            _node("a1", "doc-a", [1.0, 0.0, 0.0, 0.0]),
            _node("a2", "doc-a", [0.0, 1.0, 0.0, 0.0]),
            _node("b1", "doc-b", [0.0, 0.0, 1.0, 0.0]),
            _node("a0", "doc-a", [0.0, 0.0, 0.0, 1.0], content_hash="hash-0"),
        ],
        force_flush=True,
    )
    yield store
    client.drop_collection(collection_name)


def _rows(store: PartitionAwareMilvusVectorStore) -> dict[str, dict]:
    rows = store.client.query(
        collection_name=store.collection_name, filter='id != ""', output_fields=["*"], consistency_level="Strong"
    )
    return {row["id"]: row for row in rows}


def test_only_the_nodes_of_that_version_of_the_document_get_the_metadata(vector_store) -> None:
    """A node of another content hash is another version of the document, e.g. one ingestion wrote meanwhile."""
    rewritten = vector_store.rewrite_document_metadata(
        "doc-a", _NAMESPACE, "hash-1", _CLASSIFICATION, list(_CLASSIFICATION)
    )

    rows = _rows(vector_store)
    assert sorted(node_id for node_ids in rewritten.values() for node_id in node_ids) == ["a1", "a2"]
    assert rows["a1"]["document_issuer"] == rows["a2"]["document_issuer"] == "Hooli AG"
    assert "document_issuer" not in rows["b1"]
    assert "document_issuer" not in rows["a0"]


def test_the_rebuilt_node_carries_the_metadata_kept_out_of_its_embedded_text(vector_store) -> None:
    vector_store.rewrite_document_metadata("doc-a", _NAMESPACE, "hash-1", _CLASSIFICATION, list(_CLASSIFICATION))

    row = _rows(vector_store)["a1"]
    node = metadata_dict_to_node(row)
    assert node.metadata["document_type"] == "invoice"
    assert node.metadata["project"] == "ABC"
    assert node.excluded_embed_metadata_keys == ["project", *_CLASSIFICATION]
    assert "document_type" not in node.get_content(metadata_mode="embed")


def test_the_vectors_and_text_are_left_as_they_were(vector_store) -> None:
    before = _rows(vector_store)["a1"]

    vector_store.rewrite_document_metadata("doc-a", _NAMESPACE, "hash-1", _CLASSIFICATION, list(_CLASSIFICATION))

    after = _rows(vector_store)["a1"]
    assert after["embedding"] == pytest.approx(before["embedding"])
    assert after["text"] == before["text"]
    assert json.loads(after["_node_content"])["text"] == json.loads(before["_node_content"])["text"]


def test_rewriting_twice_does_not_repeat_the_excluded_keys(vector_store) -> None:
    for _ in range(2):
        vector_store.rewrite_document_metadata("doc-a", _NAMESPACE, "hash-1", _CLASSIFICATION, list(_CLASSIFICATION))

    node = metadata_dict_to_node(_rows(vector_store)["a1"])
    assert node.excluded_embed_metadata_keys == ["project", *_CLASSIFICATION]
