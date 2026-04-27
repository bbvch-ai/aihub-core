from time import sleep, time

import pytest
from llama_index.core.schema import Document, NodeRelationship, NodeWithScore, RelatedNodeInfo
from pytest_bdd import given, parsers, scenarios, then, when

from swiss_ai_hub.core.generative_ai.processors.vector_prev_next_post_processor import VectorPrevNextPostProcessor
from swiss_ai_hub.core.generative_ai.resources.models.llm.embedding_model_config import EmbeddingModelConfig
from swiss_ai_hub.core.persistence.rag.documents.stores.docstore import create_mongo_document_store
from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import (
    CREATED_AT,
    DOCUMENT_ID,
    INSERTED_AT,
    NAMESPACE,
    UPDATED_AT,
)
from swiss_ai_hub.core.persistence.rag.vectors.stores.milvus_vector_store_config import MilvusVectorStoreConfig
from swiss_ai_hub.core.testing.milvus_vector_store_content import drop_collection, fill_collection, run_with_event_loop

scenarios("features/vector_prev_next_post_processor.feature")


def get_node_ids(result):
    if isinstance(result, dict):
        return list(result.keys())
    elif isinstance(result, list):
        return [n.node.node_id for n in result]
    return []


@given("these nodes:", target_fixture="nodes")
def _(datatable):
    nodes = []
    for row in datatable[1:]:
        metadata = {
            NAMESPACE: "test",
            DOCUMENT_ID: row[0],
            CREATED_AT: int(time()),
            UPDATED_AT: int(time()),
            INSERTED_AT: int(time()),
        }
        nodes.append(Document(id_=row[0], text=row[1], metadata=metadata))
    return nodes


@given(parsers.parse('the following relationships for "{node_id}":'), target_fixture="nodes_with_relationships")
def _(nodes, node_id, datatable):
    target_node = [node for node in nodes if node.id_ == node_id][0]
    for row in datatable:
        if row[0] == "previous":
            target_node.relationships[NodeRelationship.PREVIOUS] = RelatedNodeInfo(node_id=row[1])
        elif row[0] == "next":
            target_node.relationships[NodeRelationship.NEXT] = RelatedNodeInfo(node_id=row[1])
    return nodes


@pytest.fixture()
def milvus_vector_store(nodes_with_relationships):
    collection_name = "prev_next_test"

    # Drop existing collection to ensure clean schema
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
        doc_store,
        nodes=nodes_with_relationships,
    )
    sleep(1)
    yield vector_store
    drop_collection(collection_name=collection_name)


@given("a valid vector store with all nodes", target_fixture="vector_store")
def _(milvus_vector_store):
    return run_with_event_loop(milvus_vector_store.to_llama_index)


@given(parsers.parse('starting node is "{target_node_id}"'), target_fixture="starting_node")
def _(target_node_id, nodes_with_relationships):
    start_node = [node for node in nodes_with_relationships if node.node_id == target_node_id][0]
    return NodeWithScore(node=start_node, score=1.0)


@pytest.fixture
def test_context():
    return {}


@when(
    parsers.parse(
        "I postprocess nodes from the starting node using the VectorPrevNextPostProcessor "
        'with mode "{mode}" and num_nodes set to {num_nodes:d}'
    )
)
def postprocess_nodes(starting_node, vector_store, test_context, mode, num_nodes):
    processor = VectorPrevNextPostProcessor(vectorstore=vector_store, num_nodes=num_nodes, mode=mode)
    result = processor.postprocess_nodes([starting_node])
    test_context["result"] = result


@then(
    parsers.parse("the resulting node chain should contain nodes in the following order:"),
)
def check_node_chain(test_context, datatable):
    expected_ids = [row[0] for row in datatable[1:]]

    result = test_context.get("result")
    result_ids = get_node_ids(result)
    assert result_ids == expected_ids, f"Expected order {expected_ids}, got {result_ids}"
