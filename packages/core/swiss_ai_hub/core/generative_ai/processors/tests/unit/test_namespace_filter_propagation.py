from typing import Any
from unittest.mock import MagicMock

from llama_index.core.schema import NodeRelationship, NodeWithScore, RelatedNodeInfo, TextNode
from llama_index.core.vector_stores import MetadataFilter, MetadataFilters

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


class TestParentSummaryPostProcessorNamespaceFilter:
    def test_forwards_namespace_as_metadata_filter(self) -> None:
        parent = TextNode(id_="parent", text="parent", metadata={TYPE: NODE_TYPE_SUMMARY, NAMESPACE: "tenant-a"})
        child = TextNode(id_="child", text="child", metadata={NAMESPACE: "tenant-a"})
        child.relationships[NodeRelationship.PARENT] = RelatedNodeInfo(node_id="parent")

        store = _make_vector_store([parent])
        processor = ParentSummaryPostProcessor.model_construct(vectorstore=store, max_levels=1)

        processor.postprocess_nodes(nodes=[NodeWithScore(node=child, score=1.0)])

        store.get_nodes.assert_called_once()
        _, kwargs = store.get_nodes.call_args
        filters = kwargs["filters"]
        assert isinstance(filters, MetadataFilters)
        assert filters.filters == [MetadataFilter(key=NAMESPACE, value="tenant-a")]

    def test_passes_none_filters_when_namespace_missing(self) -> None:
        parent = TextNode(id_="parent", text="parent", metadata={TYPE: NODE_TYPE_SUMMARY})
        child = TextNode(id_="child", text="child", metadata={})
        child.relationships[NodeRelationship.PARENT] = RelatedNodeInfo(node_id="parent")

        store = _make_vector_store([parent])
        processor = ParentSummaryPostProcessor.model_construct(vectorstore=store, max_levels=1)

        processor.postprocess_nodes(nodes=[NodeWithScore(node=child, score=1.0)])

        _, kwargs = store.get_nodes.call_args
        assert kwargs["filters"] is None


class TestVectorPrevNextNamespaceFilter:
    def test_forwards_namespace_as_metadata_filter(self) -> None:
        seed = TextNode(id_="n1", text="seed", metadata={NAMESPACE: "tenant-b"})
        neighbour = TextNode(id_="n2", text="next", metadata={NAMESPACE: "tenant-b"})
        seed.relationships[NodeRelationship.NEXT] = RelatedNodeInfo(node_id="n2")

        store = _make_vector_store([neighbour])

        traverse_nodes(NodeWithScore(node=seed, score=1.0), num_nodes=1, vectorstore=store, direction=ModeOptions.NEXT)

        store.get_nodes.assert_called_once()
        _, kwargs = store.get_nodes.call_args
        filters = kwargs["filters"]
        assert isinstance(filters, MetadataFilters)
        assert filters.filters == [MetadataFilter(key=NAMESPACE, value="tenant-b")]

    def test_passes_none_filters_when_namespace_missing(self) -> None:
        seed = TextNode(id_="n1", text="seed", metadata={})
        neighbour = TextNode(id_="n2", text="next", metadata={})
        seed.relationships[NodeRelationship.NEXT] = RelatedNodeInfo(node_id="n2")

        store = _make_vector_store([neighbour])

        traverse_nodes(NodeWithScore(node=seed, score=1.0), num_nodes=1, vectorstore=store, direction=ModeOptions.NEXT)

        _, kwargs = store.get_nodes.call_args
        assert kwargs["filters"] is None
