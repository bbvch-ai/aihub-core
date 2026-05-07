from typing import Any
from unittest.mock import MagicMock

from llama_index.core.schema import NodeRelationship, NodeWithScore, RelatedNodeInfo, TextNode

from swiss_ai_hub.core.generative_ai.processors.parent_summary_post_processor import ParentSummaryPostProcessor
from swiss_ai_hub.core.generative_ai.processors.vector_prev_next_post_processor import (
    ModeOptions,
    traverse_nodes,
)
from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import NAMESPACE, NODE_TYPE_SUMMARY, TYPE


def _make_vector_store(return_nodes: list[TextNode]) -> Any:
    store = MagicMock()
    store.get_nodes.return_value = return_nodes
    return store


class TestParentSummaryPostProcessorPartitionScoping:
    def test_forwards_namespace_as_namespaces_kwarg(self) -> None:
        parent = TextNode(id_="parent", text="parent", metadata={TYPE: NODE_TYPE_SUMMARY, NAMESPACE: "tenant-a"})
        child = TextNode(id_="child", text="child", metadata={NAMESPACE: "tenant-a"})
        child.relationships[NodeRelationship.PARENT] = RelatedNodeInfo(node_id="parent")

        store = _make_vector_store([parent])
        processor = ParentSummaryPostProcessor.model_construct(vectorstore=store, max_levels=1)

        processor.postprocess_nodes(nodes=[NodeWithScore(node=child, score=1.0)])

        store.get_nodes.assert_called_once()
        _, kwargs = store.get_nodes.call_args
        assert kwargs["namespaces"] == ["tenant-a"]
        assert "filters" not in kwargs
        assert "milvus_partition_names" not in kwargs

    def test_omits_namespaces_when_namespace_missing(self) -> None:
        parent = TextNode(id_="parent", text="parent", metadata={TYPE: NODE_TYPE_SUMMARY})
        child = TextNode(id_="child", text="child", metadata={})
        child.relationships[NodeRelationship.PARENT] = RelatedNodeInfo(node_id="parent")

        store = _make_vector_store([parent])
        processor = ParentSummaryPostProcessor.model_construct(vectorstore=store, max_levels=1)

        processor.postprocess_nodes(nodes=[NodeWithScore(node=child, score=1.0)])

        _, kwargs = store.get_nodes.call_args
        assert "namespaces" not in kwargs

    def test_empty_string_namespace_is_treated_as_unscoped(self) -> None:
        parent = TextNode(id_="parent", text="parent", metadata={TYPE: NODE_TYPE_SUMMARY, NAMESPACE: ""})
        child = TextNode(id_="child", text="child", metadata={NAMESPACE: ""})
        child.relationships[NodeRelationship.PARENT] = RelatedNodeInfo(node_id="parent")

        store = _make_vector_store([parent])
        processor = ParentSummaryPostProcessor.model_construct(vectorstore=store, max_levels=1)

        processor.postprocess_nodes(nodes=[NodeWithScore(node=child, score=1.0)])

        _, kwargs = store.get_nodes.call_args
        assert "namespaces" not in kwargs


class TestTraverseNodesPartitionScoping:
    def test_forwards_namespace_as_namespaces_kwarg(self) -> None:
        seed = TextNode(id_="n1", text="seed", metadata={NAMESPACE: "tenant-b"})
        neighbour = TextNode(id_="n2", text="next", metadata={NAMESPACE: "tenant-b"})
        seed.relationships[NodeRelationship.NEXT] = RelatedNodeInfo(node_id="n2")

        store = _make_vector_store([neighbour])

        traverse_nodes(NodeWithScore(node=seed, score=1.0), num_nodes=1, vectorstore=store, direction=ModeOptions.NEXT)

        store.get_nodes.assert_called_once()
        _, kwargs = store.get_nodes.call_args
        assert kwargs["namespaces"] == ["tenant-b"]
        assert "filters" not in kwargs
        assert "milvus_partition_names" not in kwargs

    def test_omits_namespaces_when_namespace_missing(self) -> None:
        seed = TextNode(id_="n1", text="seed", metadata={})
        neighbour = TextNode(id_="n2", text="next", metadata={})
        seed.relationships[NodeRelationship.NEXT] = RelatedNodeInfo(node_id="n2")

        store = _make_vector_store([neighbour])

        traverse_nodes(NodeWithScore(node=seed, score=1.0), num_nodes=1, vectorstore=store, direction=ModeOptions.NEXT)

        _, kwargs = store.get_nodes.call_args
        assert "namespaces" not in kwargs

    def test_empty_string_namespace_is_treated_as_unscoped(self) -> None:
        seed = TextNode(id_="n1", text="seed", metadata={NAMESPACE: ""})
        neighbour = TextNode(id_="n2", text="next", metadata={NAMESPACE: ""})
        seed.relationships[NodeRelationship.NEXT] = RelatedNodeInfo(node_id="n2")

        store = _make_vector_store([neighbour])

        traverse_nodes(NodeWithScore(node=seed, score=1.0), num_nodes=1, vectorstore=store, direction=ModeOptions.NEXT)

        _, kwargs = store.get_nodes.call_args
        assert "namespaces" not in kwargs

    def test_forwards_namespace_for_previous_direction(self) -> None:
        seed = TextNode(id_="n2", text="seed", metadata={NAMESPACE: "tenant-c"})
        neighbour = TextNode(id_="n1", text="prev", metadata={NAMESPACE: "tenant-c"})
        seed.relationships[NodeRelationship.PREVIOUS] = RelatedNodeInfo(node_id="n1", metadata={"index": 1})

        store = _make_vector_store([neighbour])

        traverse_nodes(
            NodeWithScore(node=seed, score=1.0), num_nodes=1, vectorstore=store, direction=ModeOptions.PREVIOUS
        )

        _, kwargs = store.get_nodes.call_args
        assert kwargs["namespaces"] == ["tenant-c"]
