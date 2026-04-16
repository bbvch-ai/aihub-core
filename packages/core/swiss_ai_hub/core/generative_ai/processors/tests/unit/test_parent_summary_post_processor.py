from time import sleep, time

import pytest
from llama_index.core.schema import Document, NodeRelationship, NodeWithScore, RelatedNodeInfo
from pytest_bdd import given, parsers, scenarios, then, when

from swiss_ai_hub.core.generative_ai.processors.parent_summary_post_processor import ParentSummaryPostProcessor
from swiss_ai_hub.core.generative_ai.resources.models.llm.embedding_model_config import EmbeddingModelConfig
from swiss_ai_hub.core.persistence.rag.documents.stores.docstore import create_mongo_document_store
from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import (
    CREATED_AT,
    DOCUMENT_ID,
    INSERTED_AT,
    NAMESPACE,
    NODE_TYPE_SUMMARY,
    TYPE,
    UPDATED_AT,
)
from swiss_ai_hub.core.persistence.rag.vectors.stores.milvus_vector_store_config import MilvusVectorStoreConfig
from swiss_ai_hub.core.testing.milvus_vector_store_content import drop_collection, fill_collection, run_with_event_loop
from swiss_ai_hub.core.testing.auth_utils.user_mocks import mock_keycloak_admin_service_autouse  # noqa: F401


scenarios("features/parent_summary_post_processor.feature")


@given("these nodes:", target_fixture="nodes")
def _(datatable):
    nodes = []
    for row in datatable:
        node_type = row[2] if len(row) > 2 else "content"
        metadata = {
            NAMESPACE: "test",
            DOCUMENT_ID: row[0],
            CREATED_AT: int(time()),
            UPDATED_AT: int(time()),
            INSERTED_AT: int(time()),
        }
        if node_type == "summary":
            metadata[TYPE] = NODE_TYPE_SUMMARY
        nodes.append(Document(id_=row[0], text=row[1], metadata=metadata))
    return nodes


@given(parsers.parse("the following parent relationships:"), target_fixture="nodes_with_relationships")
def _(nodes, datatable):
    for row in datatable:
        node_id = row[0]
        parent_id = row[1]

        target_node = next((node for node in nodes if node.id_ == node_id), None)
        if target_node:
            target_node.relationships[NodeRelationship.PARENT] = RelatedNodeInfo(node_id=parent_id)

    return nodes


@pytest.fixture()
def milvus_vector_store(nodes_with_relationships):
    collection_name = "parent_summary_test"

    drop_collection(collection_name=collection_name)

    embedding_config = EmbeddingModelConfig(model_name="embedding/bge-m3")

    vector_store = MilvusVectorStoreConfig(
        uri="http://localhost:19530",
        collection_name=collection_name,
        dimensions=1024,
    )
    doc_store = create_mongo_document_store(document_store_name="development")

    fill_collection(
        embedding_config,
        vector_store,
        doc_store=doc_store,
        nodes=nodes_with_relationships,
    )
    sleep(1)
    yield vector_store
    drop_collection(collection_name=collection_name)


@given("a valid vector store with all nodes", target_fixture="vector_store")
def _(milvus_vector_store):
    return run_with_event_loop(milvus_vector_store.to_llama_index)


@given(parsers.parse("starting nodes are:"), target_fixture="starting_nodes")
def _(datatable, nodes_with_relationships):
    result = []
    for row in datatable[1:]:  # Skip header row
        node_id = row[0]
        node = next((n for n in nodes_with_relationships if n.node_id == node_id), None)
        if node:
            result.append(NodeWithScore(node=node, score=1.0))
    return result


@pytest.fixture
def context():
    return {}


@when(parsers.parse("I postprocess nodes using the ParentSummaryPostProcessor with max_levels set to {max_levels:d}"))
def postprocess_nodes(starting_nodes, vector_store, context, max_levels):
    processor = ParentSummaryPostProcessor(vectorstore=vector_store, max_levels=max_levels)
    result = processor.postprocess_nodes(nodes=starting_nodes)
    context["result"] = result


@then(
    parsers.parse("the resulting nodes should include:"),
)
def check_resulting_nodes(context, datatable):
    expected_ids = set(row[0] for row in datatable[1:])  # Skip header row

    result = context.get("result")
    result_ids = set(node.node.node_id for node in result)

    assert expected_ids.issubset(result_ids), f"Expected nodes {expected_ids} to be included in {result_ids}"

    # Make sure we have all expected nodes (not more, not less)
    assert expected_ids == result_ids, f"Expected exactly {expected_ids}, got {result_ids}"
