from enum import StrEnum
from typing import Annotated, Any

from llama_index.core.postprocessor.types import BaseNodePostprocessor
from llama_index.core.schema import NodeWithScore, QueryBundle
from llama_index.core.vector_stores.types import BasePydanticVectorStore
from pydantic import Field, field_validator

from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import INDEX, NAMESPACE


class ModeOptions(StrEnum):
    NEXT = "next"
    PREVIOUS = "previous"
    BOTH = "both"


def traverse_nodes(
    node_with_score: NodeWithScore,
    num_nodes: int,
    vectorstore: BasePydanticVectorStore,
    direction: ModeOptions,
) -> dict[str, NodeWithScore]:
    """
    Traverses nodes in a chain either forward or backward.
    For backward traversal, if the metadata INDEX equals 0, the chain stops.
    """
    nodes = {node_with_score.node.node_id: node_with_score}
    current_node = node_with_score.node

    # Scope neighbour fetches to the source node's namespace so partition-aware stores
    # avoid loading the whole collection. Empty-string namespace (DEFAULT_METADATA) is
    # treated as unscoped.
    namespace: str | None = current_node.metadata.get(NAMESPACE)
    scope_kwargs: dict[str, Any] = {"namespaces": [namespace]} if namespace else {}

    for _ in range(num_nodes):
        relation = current_node.next_node if direction == ModeOptions.NEXT else current_node.prev_node
        if not relation:
            break
        # For backward direction, check the INDEX metadata value
        if direction == ModeOptions.PREVIOUS and relation.metadata.get(INDEX) == 0:
            break
        current_node = vectorstore.get_nodes([relation.node_id], **scope_kwargs)[0]
        nodes[current_node.node_id] = NodeWithScore(node=current_node)
    return nodes


def get_forward_nodes(
    node_with_score: NodeWithScore, num_nodes: int, vectorstore: BasePydanticVectorStore
) -> dict[str, NodeWithScore]:
    return traverse_nodes(node_with_score, num_nodes, vectorstore, ModeOptions.NEXT)


def get_backward_nodes(
    node_with_score: NodeWithScore, num_nodes: int, vectorstore: BasePydanticVectorStore
) -> dict[str, NodeWithScore]:
    return traverse_nodes(node_with_score, num_nodes, vectorstore, ModeOptions.PREVIOUS)


class VectorPrevNextPostProcessor(BaseNodePostprocessor):
    """
    Post-processor to fetch additional nodes from the vector store based on node relationships.
    """

    vectorstore: BasePydanticVectorStore
    num_nodes: Annotated[int, Field(description="Number of additional nodes to fetch")] = 1
    mode: Annotated[ModeOptions, Field(description="Direction to fetch nodes (NEXT, PREVIOUS, or BOTH)")] = (
        ModeOptions.NEXT
    )

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, v: ModeOptions) -> ModeOptions:
        if v not in ModeOptions:
            raise ValueError(f"Invalid mode: {v}")
        return v

    @classmethod
    def class_name(cls) -> str:
        return "VectorPrevNextPostProcessor"

    def _postprocess_nodes(
        self, nodes: list[NodeWithScore], query_bundle: QueryBundle | None = None
    ) -> list[NodeWithScore]:
        # Accumulate all nodes from the input and the forward/backward chains.
        all_nodes: dict[str, NodeWithScore] = {}
        for node in nodes:
            all_nodes[node.node.node_id] = node
            if self.mode in (ModeOptions.NEXT, ModeOptions.BOTH):
                all_nodes.update(get_forward_nodes(node, self.num_nodes, self.vectorstore))
            if self.mode in (ModeOptions.PREVIOUS, ModeOptions.BOTH):
                all_nodes.update(get_backward_nodes(node, self.num_nodes, self.vectorstore))
        all_nodes_values = list(all_nodes.values())
        return self._sort_nodes(all_nodes_values)

    def _sort_nodes(self, all_nodes_values: list[NodeWithScore]) -> list[NodeWithScore]:
        sorted_nodes: list[NodeWithScore] = []
        for node in all_nodes_values:
            node_inserted = False
            for i, cand in enumerate(sorted_nodes):
                node_id = node.node.node_id
                prev_node_info = cand.node.prev_node
                next_node_info = cand.node.next_node
                if prev_node_info is not None and node_id == prev_node_info.node_id:
                    node_inserted = True
                    sorted_nodes.insert(i, node)
                    break
                # append to current candidate
                elif next_node_info is not None and node_id == next_node_info.node_id:
                    node_inserted = True
                    sorted_nodes.insert(i + 1, node)
                    break
            if not node_inserted:
                sorted_nodes.append(node)
        return sorted_nodes
