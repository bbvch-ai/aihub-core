import asyncio
from time import sleep

import pytest
from llama_index.core.schema import Document, NodeRelationship, NodeWithScore, RelatedNodeInfo
from pytest_bdd import given, parsers, scenarios, then, when

from aihub_lib.generative_ai.processors.ParentSummaryPostProcessor import ParentSummaryPostProcessor
from aihub_lib.generative_ai.resources.models.llm.embedding.self_hosted.SelfHostedEmbeddingConfig import (
    SelfHostedEmbeddingConfig,
    SelfHostedEmbeddingParameter,
)
from aihub_lib.persistence.rag.documents.stores.MongoDocumentStoreFactory import create_mongo_document_store
from aihub_lib.persistence.rag.vectors.node_metadata import NODE_TYPE_SUMMARY, TYPE
from aihub_lib.persistence.rag.vectors.stores.MilvusVectorStoreFactory import create_milvus_vector_store
from aihub_lib.testing.milvus_vector_store_content import fill_collection


# Set up an event loop for the test session
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


scenarios("features/parent_summary_post_processor.feature")


@given("these nodes:", target_fixture="nodes")
def _(datatable):
    nodes = []
    for row in datatable:
        node_type = row[2] if len(row) > 2 else "content"
        metadata = {TYPE: NODE_TYPE_SUMMARY} if node_type == "summary" else {}
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
def milvus_vector_store(nodes_with_relationships, event_loop):
    # Use event_loop fixture to ensure there's an active event loop
    asyncio.set_event_loop(event_loop)

    embedding_config = SelfHostedEmbeddingConfig(
        name="Alibaba-NLP/gte-base-en-v1.5",
        base_url="http://localhost:8183",
        api_key=None,
        timeout=60,
        embed_batch_size=32,
        default_parameter=SelfHostedEmbeddingParameter(
            text_instruction=None,
            query_instruction=None,
            truncate_text=False,
        ),
    )

    vector_store = create_milvus_vector_store(
        uri="http://localhost",
        collection_name="parent_summary_test",
        embedding_vector_dimension=768,
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


@given("a valid vector store with all nodes", target_fixture="vector_store")
def _(milvus_vector_store):
    return milvus_vector_store


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
