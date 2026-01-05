from contextlib import contextmanager

import pytest
from llama_index.core.schema import TextNode
from pymilvus import Collection, MilvusClient, connections
from pytest_bdd import given, parsers, scenarios, then, when

from aihub_lib.persistence.rag.vectors.node_metadata import DOCUMENT_ID, NAMESPACE
from aihub_lib.persistence.rag.vectors.stores.MilvusVectorStoreFactory import (
    MilvusIndexType,
    create_milvus_vector_store,
)
from aihub_lib.testing.milvus_vector_store_content import drop_collection, ensure_event_loop

scenarios("./features/milvus_vector_store.feature")


# Fixtures
@pytest.fixture
def context():
    """Shared context dictionary for test state."""
    return {
        "milvus_uri": None,
        "embedding_dimension": None,
        "collection_name": None,
        "vector_store": None,
        "index_type": None,
        "num_partitions": 2,
        "nodes": [],
        "error": None,
        "client": None,
    }


@pytest.fixture
def milvus_client(context):
    """Reusable Milvus client."""
    if not context.get("client") and context.get("milvus_uri"):
        context["client"] = MilvusClient(uri=context["milvus_uri"])
    return context["client"]


@pytest.fixture(autouse=True)
def cleanup_test_collections(context):
    """Auto-cleanup test collections before and after each scenario."""
    yield
    # Cleanup after test
    if context.get("milvus_uri") and context.get("collection_name"):
        drop_collection(uri=context["milvus_uri"], collection_name=context["collection_name"])


# Helper functions
@contextmanager
def milvus_connection(uri: str):
    """Context manager for Milvus connections."""
    connections.connect(uri=uri)
    try:
        yield
    finally:
        connections.disconnect("default")


def _create_test_nodes(namespace: str, count: int, embedding_dim: int) -> list[TextNode]:
    """Create test nodes with specified namespace."""
    nodes = []
    for i in range(count):
        node = TextNode(
            id_=f"{namespace}_node_{i}",
            text=f"Test content for {namespace} node {i}",
            embedding=[0.1] * embedding_dim,
        )
        node.metadata = {
            NAMESPACE: namespace,
            DOCUMENT_ID: f"{namespace}_doc",
        }
        nodes.append(node)
    return nodes


def _get_embedding_index(collection: Collection):
    """Get the embedding field index from a collection."""
    return next((idx for idx in collection.indexes if idx.field_name == "embedding"), None)


def _create_vector_store(context, **kwargs):
    """Centralized vector store creation with error handling."""
    create_milvus_vector_store.cache_clear()

    defaults = {
        "uri": context["milvus_uri"],
        "collection_name": context["collection_name"],
        "embedding_vector_dimension": context["embedding_dimension"],
        "index_type": MilvusIndexType.FLAT,
    }

    with ensure_event_loop():
        context["vector_store"] = create_milvus_vector_store(**(defaults | kwargs))
    context["error"] = None


# Given steps
@given(parsers.parse('a Milvus server is running at "{uri}"'))
def given_milvus_server(context, uri: str):
    """Set Milvus connection URI."""
    context["milvus_uri"] = uri


@given(parsers.parse("the embedding dimension is {dimension:d}"))
def given_embedding_dimension(context, dimension: int):
    """Set embedding dimension."""
    context["embedding_dimension"] = dimension


@given(parsers.parse('I want to create a collection named "{collection_name}"'))
def given_collection_name(context, collection_name: str):
    """Set collection name."""
    context["collection_name"] = collection_name


@given(parsers.parse("I create a vector store with {num_partitions:d} partitions"))
def given_create_vector_store_with_partitions(context, num_partitions: int):
    """Create a vector store; num_partitions parameter is ignored and retained only for test step compatibility."""
    context["num_partitions"] = num_partitions
    _create_vector_store(context)  # Always creates with manual partitions now


# When steps
@when(parsers.parse('I create a vector store with index type "{index_type}"'))
def when_create_vector_store_with_index(context, index_type: str):
    """Create a vector store with specified index type."""
    context["index_type"] = MilvusIndexType[index_type]
    _create_vector_store(context, index_type=context["index_type"])


@when(parsers.parse("I create a vector store with {num_partitions:d} partitions"))
def when_create_vector_store(context, num_partitions: int):
    """Create a vector store with manual partitions (num_partitions parameter ignored for backward compat)."""
    context["num_partitions"] = num_partitions
    _create_vector_store(context)  # Always creates with manual partitions now


@when(parsers.parse('I insert {count:d} nodes with namespace "{namespace}"'))
def when_insert_nodes(context, count: int, namespace: str):
    """Insert nodes with specified namespace."""
    nodes = _create_test_nodes(namespace, count, context["embedding_dimension"])
    context["vector_store"].add(nodes)
    context["nodes"].extend(nodes)


@when("I flush and load the collection")
def when_flush_and_load(context, milvus_client):
    """Flush and load specific partitions (manual partitioning approach)."""
    from aihub_lib.persistence.rag.vectors.stores.MilvusPartitionManager import get_partition_name_for_namespace

    milvus_client.flush(collection_name=context["collection_name"])

    # Load only the partitions that contain data (memory-efficient)
    namespaces = {node.metadata.get(NAMESPACE) for node in context["nodes"] if node.metadata.get(NAMESPACE)}
    partition_names = [get_partition_name_for_namespace(ns) for ns in namespaces]
    milvus_client.load_partitions(collection_name=context["collection_name"], partition_names=partition_names)


@when("I create the same vector store again")
def when_create_same_vector_store(context):
    """Create the same vector store again (test idempotency)."""
    _create_vector_store(context)


# Then steps
@then("the collection should exist in Milvus")
def then_collection_exists(context, milvus_client):
    """Verify collection exists."""
    assert milvus_client.has_collection(
        context["collection_name"]
    ), f"Collection {context['collection_name']} does not exist"


@then(parsers.parse('the embedding field should have index type "{expected_index_type}"'))
def then_embedding_field_has_index_type(context, expected_index_type: str):
    """Verify embedding field has specified index type."""
    with milvus_connection(context["milvus_uri"]):
        collection = Collection(context["collection_name"])
        embedding_index = _get_embedding_index(collection)

        assert embedding_index, "Embedding field index not found"
        assert (
            embedding_index.params.get("index_type") == expected_index_type
        ), f"Expected {expected_index_type}, got {embedding_index.params.get('index_type')}"


@then(parsers.parse('the sparse_embedding field should have index type "{expected_index_type}"'))
def then_sparse_embedding_field_has_index_type(context, expected_index_type: str):
    """Verify sparse_embedding field has specified index type."""
    with milvus_connection(context["milvus_uri"]):
        collection = Collection(context["collection_name"])
        sparse_index = next((idx for idx in collection.indexes if idx.field_name == "sparse_embedding"), None)

        assert sparse_index, "Sparse embedding field index not found"
        assert (
            sparse_index.params.get("index_type") == expected_index_type
        ), f"Expected {expected_index_type}, got {sparse_index.params.get('index_type')}"


@then("the namespace field should be the partition key")
def then_namespace_is_the_partition_key(context):
    """Verify namespace field is configured as partition key."""
    with milvus_connection(context["milvus_uri"]):
        collection = Collection(context["collection_name"])
        namespace_field = next((f for f in collection.schema.fields if f.name == NAMESPACE), None)

        assert namespace_field, "Namespace field not found"
        assert namespace_field.is_partition_key, "Namespace field must be partition key"


@then("the collection schema should have these fields:")
def then_schema_has_fields(context, datatable):
    """Verify collection schema has all specified fields with correct properties."""
    with milvus_connection(context["milvus_uri"]):
        collection = Collection(context["collection_name"])
        schema = collection.schema

        for row in datatable[1:]:  # Skip header row
            field_name, data_type, is_primary, is_partition_key = row
            field = next((f for f in schema.fields if f.name == field_name), None)

            assert field, f"Field '{field_name}' not found in schema"

            # Handle dtype - can be enum name or numeric value
            actual_dtype = field.dtype.name if hasattr(field.dtype, "name") else str(field.dtype).split(".")[-1]
            assert (
                actual_dtype == data_type
            ), f"Field '{field_name}' type mismatch: expected {data_type}, got {actual_dtype} (raw: {field.dtype})"
            assert field.is_primary == (is_primary == "true"), f"Field '{field_name}' is_primary mismatch"
            assert field.is_partition_key == (
                is_partition_key == "true"
            ), f"Field '{field_name}' is_partition_key mismatch"


@then("the collection should have a BM25 function defined")
def then_collection_has_bm25_function(context):
    """Verify collection has BM25 function for sparse embeddings."""
    with milvus_connection(context["milvus_uri"]):
        collection = Collection(context["collection_name"])
        functions = collection.schema.functions

        bm25_fn = next((f for f in functions if f.name == "bm25_fn"), None)
        assert bm25_fn, "BM25 function not found in schema"
        assert bm25_fn.input_field_names == ["text"], "BM25 input should be 'text' field"
        assert bm25_fn.output_field_names == ["sparse_embedding"], "BM25 output should be 'sparse_embedding'"


@then(parsers.parse('the collection should have index type "{expected_index_type}"'))
def then_collection_has_index_type(context, expected_index_type: str):
    """Verify collection has specified index type."""
    with milvus_connection(context["milvus_uri"]):
        collection = Collection(context["collection_name"])
        embedding_index = _get_embedding_index(collection)

        assert embedding_index, "Embedding field index not found"

        actual_index_type = embedding_index.params.get("index_type")
        assert (
            actual_index_type == expected_index_type
        ), f"Expected index type {expected_index_type}, got {actual_index_type}"


@then("the namespace field should be marked as partition key")
def then_namespace_is_partition_key(context):
    """Verify namespace field is partition key."""
    with milvus_connection(context["milvus_uri"]):
        collection = Collection(context["collection_name"])
        namespace_field = next((field for field in collection.schema.fields if field.name == NAMESPACE), None)

        assert namespace_field, f"Namespace field '{NAMESPACE}' not found in schema"
        assert namespace_field.is_partition_key, "Namespace field should be marked as partition key"


@then(parsers.parse("the collection should have {expected_count:d} physical partitions"))
def then_collection_has_partitions(context, milvus_client, expected_count: int):
    """Verify number of physical partitions."""
    partitions = milvus_client.list_partitions(collection_name=context["collection_name"])
    assert len(partitions) == expected_count, f"Expected {expected_count} partitions, got {len(partitions)}"


@then(parsers.parse('querying for namespace "{namespace}" should return {expected_count:d} nodes'))
def then_query_namespace_returns_nodes(context, namespace: str, expected_count: int, milvus_client):
    """Verify querying by namespace returns expected number of nodes."""
    results = milvus_client.query(
        collection_name=context["collection_name"],
        filter=f'{NAMESPACE} == "{namespace}"',
        output_fields=["id", NAMESPACE],
        limit=100,
    )

    assert (
        len(results) == expected_count
    ), f"Expected {expected_count} nodes for namespace {namespace}, got {len(results)}"


@then(parsers.parse("the data should be distributed across {expected_partitions:d} physical partitions"))
def then_data_distributed_across_partitions(context, expected_partitions: int, milvus_client):
    """Verify data is distributed across physical partitions."""
    partitions = milvus_client.list_partitions(collection_name=context["collection_name"])

    assert (
        len(partitions) == expected_partitions
    ), f"Expected {expected_partitions} physical partitions, got {len(partitions)}"

    # Verify all data is accessible
    all_results = milvus_client.query(
        collection_name=context["collection_name"],
        filter="id != ''",
        output_fields=["id", NAMESPACE],
        limit=2000,
    )

    assert len(all_results) > 0, "No data found in collection"


@then("the vector store should have sparse embeddings enabled")
def then_sparse_embeddings_enabled(context):
    """Verify sparse embeddings are enabled."""
    assert context["vector_store"].enable_sparse is True, "Sparse embeddings should be enabled"


@then(parsers.parse('the collection schema should have a "{field_name}" field'))
def then_schema_has_field(context, field_name: str):
    """Verify collection schema has specified field."""
    with milvus_connection(context["milvus_uri"]):
        collection = Collection(context["collection_name"])
        field_found = any(field.name == field_name for field in collection.schema.fields)
        assert field_found, f"Field '{field_name}' not found in schema"


@then("no error should have occurred")
def then_no_error(context):
    """Verify no error occurred."""
    assert context["error"] is None, f"Unexpected error occurred: {context['error']}"


@then(parsers.parse('all returned nodes should have namespace "{expected_namespace}"'))
def then_all_nodes_have_namespace(context, expected_namespace: str, milvus_client):
    """Verify all returned nodes have the expected namespace."""
    results = milvus_client.query(
        collection_name=context["collection_name"],
        filter=f'{NAMESPACE} == "{expected_namespace}"',
        output_fields=["id", NAMESPACE],
        limit=100,
    )

    for result in results:
        assert (
            result[NAMESPACE] == expected_namespace
        ), f"Expected namespace {expected_namespace}, got {result[NAMESPACE]}"


@then("all returned nodes should have their correct namespace")
def then_all_nodes_have_correct_namespace(context, milvus_client):
    """Verify each namespace has correct nodes (no cross-contamination)."""
    # Get all unique namespaces from inserted nodes
    namespaces = {node.metadata.get(NAMESPACE) for node in context["nodes"]}

    for namespace in namespaces:
        results = milvus_client.query(
            collection_name=context["collection_name"],
            filter=f'{NAMESPACE} == "{namespace}"',
            output_fields=["id", NAMESPACE],
            limit=100,
        )

        assert len(results) > 0, f"No results found for namespace '{namespace}'"

        for result in results:
            assert (
                result[NAMESPACE] == namespace
            ), f"Namespace mismatch: expected '{namespace}', got '{result[NAMESPACE]}'"
