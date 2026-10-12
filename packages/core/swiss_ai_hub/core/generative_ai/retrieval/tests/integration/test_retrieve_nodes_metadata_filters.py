"""Runtime metadata filters against a real Milvus: a value is found whether a document stored it alone or in a list."""

import uuid
from collections.abc import Iterator
from unittest.mock import MagicMock

import pytest
from llama_index.core.schema import TextNode
from llama_index.core.vector_stores.types import BasePydanticVectorStore, VectorStoreQueryMode
from pymilvus import MilvusClient

from swiss_ai_hub.core.generative_ai.retrieval.retrieve_nodes import retrieve_nodes
from swiss_ai_hub.core.generative_ai.retrievers.metadata_filter_pair import MetadataFilterPair
from swiss_ai_hub.core.infrastructure.milvus.milvus_settings import MilvusSettings
from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import NAMESPACE, NODE_TYPE_CONTENT, TYPE
from swiss_ai_hub.core.persistence.rag.vectors.stores.milvus_vector_store_factory import create_milvus_vector_store

pytestmark = pytest.mark.integration

_NAMESPACE = "jira"
_DIMENSION = 4

# Shaped as ingestion stores frontmatter: lists and flags as text, numbers as numbers.
_DOCUMENTS: dict[str, dict[str, str | int | list[str]]] = {
    "list_doc": {"project": "ABC", "labels": ["backend", "urgent"], "draft": "true"},
    "text_doc": {"project": "XYZ", "labels": "backend", "priority": 2},
    "no_labels_doc": {"project": "ABC"},
}


@pytest.fixture(scope="module")
def vector_store() -> Iterator[BasePydanticVectorStore]:
    settings = MilvusSettings()
    client = MilvusClient(uri=settings.URL, token=settings.get_token())
    collection_name = f"metadata_filters_{uuid.uuid4().hex[:8]}"
    store = create_milvus_vector_store(
        client=client,
        collection_name=collection_name,
        embedding_vector_dimension=_DIMENSION,
        uri=settings.URL,
        token=settings.get_token(),
    )
    store.add(
        [
            TextNode(
                id_=document_id,
                text=f"Text of {document_id}",
                embedding=[1.0] * _DIMENSION,
                metadata={NAMESPACE: _NAMESPACE, TYPE: NODE_TYPE_CONTENT, **fields},
            )
            for document_id, fields in _DOCUMENTS.items()
        ],
        force_flush=True,
    )
    yield store
    client.drop_collection(collection_name)


def _matching(vector_store: BasePydanticVectorStore, *filters: MetadataFilterPair) -> set[str]:
    embed_model = MagicMock()
    embed_model.get_text_embedding.return_value = [1.0] * _DIMENSION
    nodes = retrieve_nodes(
        message="login problems",
        embed_model=embed_model,
        retrieve_k=10,
        index_namespaces=[_NAMESPACE],
        query_mode=VectorStoreQueryMode.DEFAULT,
        node_types=[NODE_TYPE_CONTENT],
        vector_store=vector_store,
        additional_filters=list(filters),
    )
    return {node.node.node_id for node in nodes}


class TestMetadataFiltersInMilvus:
    def test_a_text_value_is_found_alone_or_in_a_list(self, vector_store: BasePydanticVectorStore) -> None:
        assert _matching(vector_store, MetadataFilterPair(key="labels", value="backend")) == {"list_doc", "text_doc"}

    def test_a_value_only_one_list_holds_finds_only_that_document(self, vector_store: BasePydanticVectorStore) -> None:
        assert _matching(vector_store, MetadataFilterPair(key="labels", value="urgent")) == {"list_doc"}

    def test_a_scalar_filter_matches_equal_values_only(self, vector_store: BasePydanticVectorStore) -> None:
        assert _matching(vector_store, MetadataFilterPair(key="project", value="ABC")) == {"list_doc", "no_labels_doc"}

    def test_a_number_matches_by_equality(self, vector_store: BasePydanticVectorStore) -> None:
        assert _matching(vector_store, MetadataFilterPair(key="priority", value=2)) == {"text_doc"}

    def test_a_flag_matches_the_text_ingestion_stores(self, vector_store: BasePydanticVectorStore) -> None:
        assert _matching(vector_store, MetadataFilterPair(key="draft", value=True)) == {"list_doc"}

    def test_filters_combine_with_and(self, vector_store: BasePydanticVectorStore) -> None:
        filters = (MetadataFilterPair(key="project", value="ABC"), MetadataFilterPair(key="labels", value="backend"))

        assert _matching(vector_store, *filters) == {"list_doc"}
