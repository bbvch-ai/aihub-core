"""Classification metadata against a real Milvus: stored as ingestion stores it, filterable by type and value (#2482).

The metadata comes from `DocumentClassification.to_metadata()`, so it carries what Milvus' dynamic field has to hold:
explicit nulls for unknown values, lists for types and references, floats for amounts.
"""

import uuid
from collections.abc import Iterator
from typing import Any
from unittest.mock import MagicMock

import pytest
from llama_index.core.schema import TextNode
from llama_index.core.vector_stores.types import BasePydanticVectorStore, VectorStoreQueryMode
from pymilvus import MilvusClient

from swiss_ai_hub.core.generative_ai.document.classification.document_classification import DocumentClassification
from swiss_ai_hub.core.generative_ai.document.classification.document_classification_answer import (
    DocumentClassificationAnswer,
)
from swiss_ai_hub.core.generative_ai.document.classification.document_type import DocumentType
from swiss_ai_hub.core.generative_ai.retrieval.retrieve_nodes import retrieve_nodes
from swiss_ai_hub.core.generative_ai.retrievers.metadata_filter_pair import MetadataFilterPair
from swiss_ai_hub.core.infrastructure.milvus.milvus_settings import MilvusSettings
from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import NAMESPACE, NODE_TYPE_CONTENT, TYPE
from swiss_ai_hub.core.persistence.rag.vectors.stores.milvus_vector_store_factory import create_milvus_vector_store

pytestmark = pytest.mark.integration

_NAMESPACE = "finance"
_DIMENSION = 4
_UNKNOWN = dict.fromkeys(set(DocumentClassificationAnswer.model_fields) - {"document_type", "secondary_types"})


def _classified(document_type: DocumentType, text: str, **copied: Any) -> dict[str, Any]:
    answer = DocumentClassificationAnswer(**{**_UNKNOWN, **copied}, document_type=document_type, secondary_types=[])
    return DocumentClassification.from_answer(answer, text).to_metadata()


_HOOLI = "Hooli AG · Rechnung RE-1 · 14. März 2025 · Total CHF 12'496.36"
_ALPEN = "Alpenglück Bürobedarf AG · Rechnung 2025-1142 · Total CHF 1'082.08"
_DOCUMENTS: dict[str, dict[str, Any]] = {
    "hooli_invoice": _classified(
        DocumentType.INVOICE,
        _HOOLI,
        document_issuer="Hooli AG",
        document_reference_number="RE-1",
        document_date="14. März 2025",
        document_total_amount="CHF 12'496.36",
    ),
    "alpen_invoice": _classified(
        DocumentType.INVOICE,
        _ALPEN,
        document_issuer="Alpenglück Bürobedarf AG",
        document_total_amount="CHF 1'082.08",
    ),
    "offer": _classified(DocumentType.OTHER, "Offerte OF-1 von Hooli AG"),
    "unclassified": {},
}


@pytest.fixture(scope="module")
def vector_store() -> Iterator[BasePydanticVectorStore]:
    settings = MilvusSettings()
    client = MilvusClient(uri=settings.URL, token=settings.get_token())
    collection_name = f"classification_filters_{uuid.uuid4().hex[:8]}"
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
                metadata={NAMESPACE: _NAMESPACE, TYPE: NODE_TYPE_CONTENT, **metadata},
            )
            for document_id, metadata in _DOCUMENTS.items()
        ],
        force_flush=True,
    )
    yield store
    client.drop_collection(collection_name)


def _matching(vector_store: BasePydanticVectorStore, *filters: MetadataFilterPair) -> set[str]:
    embed_model = MagicMock()
    embed_model.get_text_embedding.return_value = [1.0] * _DIMENSION
    nodes = retrieve_nodes(
        message="invoices",
        embed_model=embed_model,
        retrieve_k=10,
        index_namespaces=[_NAMESPACE],
        query_mode=VectorStoreQueryMode.DEFAULT,
        node_types=[NODE_TYPE_CONTENT],
        vector_store=vector_store,
        additional_filters=list(filters),
    )
    return {node.node.node_id for node in nodes}


class TestClassificationFiltersInMilvus:
    def test_every_node_shape_is_stored_including_nulls_lists_and_floats(
        self, vector_store: BasePydanticVectorStore
    ) -> None:
        assert _matching(vector_store) == set(_DOCUMENTS)

    def test_a_type_filter_finds_the_documents_listing_that_type(self, vector_store: BasePydanticVectorStore) -> None:
        assert _matching(vector_store, MetadataFilterPair(key="document_types", value="invoice")) == {
            "hooli_invoice",
            "alpen_invoice",
        }

    def test_type_and_issuer_together_find_one_invoice(self, vector_store: BasePydanticVectorStore) -> None:
        found = _matching(
            vector_store,
            MetadataFilterPair(key="document_type", value="invoice"),
            MetadataFilterPair(key="document_issuer", value="Hooli AG"),
        )

        assert found == {"hooli_invoice"}

    def test_a_stored_date_and_amount_are_found_by_value(self, vector_store: BasePydanticVectorStore) -> None:
        assert _matching(vector_store, MetadataFilterPair(key="document_date", value="2025-03-14")) == {"hooli_invoice"}
        assert _matching(vector_store, MetadataFilterPair(key="document_total_amount", value=1082.08)) == {
            "alpen_invoice"
        }
