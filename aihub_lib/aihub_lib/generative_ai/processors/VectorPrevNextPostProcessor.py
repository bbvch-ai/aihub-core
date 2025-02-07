import json
from enum import Enum
from typing import Dict, List, Optional

from llama_index.core.postprocessor.types import BaseNodePostprocessor
from llama_index.core.schema import BaseNode, NodeWithScore, QueryBundle, TextNode
from llama_index.core.vector_stores.types import BasePydanticVectorStore
from llama_index.core.vector_stores.utils import legacy_metadata_dict_to_node, metadata_dict_to_node
from pydantic import Field, field_validator

from aihub_lib.persistence.rag.vectors.node_metadata import INDEX


class ModeOptions(str, Enum):
    NEXT = "next"
    PREVIOUS = "previous"
    BOTH = "both"


def get_node(node_id: str, vectorstore: BasePydanticVectorStore) -> BaseNode:

    doc = vectorstore.client.get_document(node_id)
    node_id = doc[vectorstore._field_mapping["id"]]
    metadata_str = doc[vectorstore._field_mapping["metadata"]]
    metadata = json.loads(metadata_str) if metadata_str else {}
    chunk = doc[vectorstore._field_mapping["chunk"]]

    try:
        node = metadata_dict_to_node(metadata)
        node.set_content(chunk)
        return node
    except Exception:
        # Backward compatibility with legacy logic
        metadata, node_info, relationships = legacy_metadata_dict_to_node(metadata)
        return TextNode(
            text=chunk,
            id_=node_id,
            metadata=metadata,
            start_char_idx=node_info.get("start"),
            end_char_idx=node_info.get("end"),
            relationships=relationships,
        )


def traverse_nodes(
    node_with_score: NodeWithScore,
    num_nodes: int,
    vectorstore: BasePydanticVectorStore,
    direction: ModeOptions,
) -> Dict[str, NodeWithScore]:
    """
    Traverses nodes in a chain either forward or backward.
    For backward traversal, if the metadata INDEX equals 0, the chain stops.
    """
    nodes = {node_with_score.node.node_id: node_with_score}
    current_node = node_with_score.node

    for _ in range(num_nodes):
        relation = current_node.next_node if direction == ModeOptions.NEXT else current_node.prev_node
        if not relation:
            break
        # For backward direction, check the INDEX metadata value
        if direction == ModeOptions.PREVIOUS and relation.metadata.get(INDEX) == 0:
            break
        current_node = get_node(relation.node_id, vectorstore)
        nodes[current_node.node_id] = NodeWithScore(node=current_node)
    return nodes


def get_forward_nodes(
    node_with_score: NodeWithScore, num_nodes: int, vectorstore: BasePydanticVectorStore
) -> Dict[str, NodeWithScore]:
    return traverse_nodes(node_with_score, num_nodes, vectorstore, ModeOptions.NEXT)


def get_backward_nodes(
    node_with_score: NodeWithScore, num_nodes: int, vectorstore: BasePydanticVectorStore
) -> Dict[str, NodeWithScore]:
    return traverse_nodes(node_with_score, num_nodes, vectorstore, ModeOptions.PREVIOUS)


class VectorPrevNextPostProcessor(BaseNodePostprocessor):
    """
    Post-processor to fetch additional nodes from the vector store based on node relationships.

    Attributes:
        vectorstore (BasePydanticVectorStore): The vector store.
        num_nodes (int): Number of additional nodes to fetch (default is 1).
        mode (ModeOptions): Direction to fetch nodes. Options are NEXT, PREVIOUS, or BOTH.
    """

    vectorstore: BasePydanticVectorStore
    num_nodes: int = Field(default=1)
    mode: ModeOptions = Field(default=ModeOptions.NEXT)

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
        self, nodes: List[NodeWithScore], query_bundle: Optional[QueryBundle] = None
    ) -> List[NodeWithScore]:
        # Accumulate all nodes from the input and the forward/backward chains.
        all_nodes: Dict[str, NodeWithScore] = {}
        for node in nodes:
            all_nodes[node.node.node_id] = node
            if self.mode in (ModeOptions.NEXT, ModeOptions.BOTH):
                all_nodes.update(get_forward_nodes(node, self.num_nodes, self.vectorstore))
            if self.mode in (ModeOptions.PREVIOUS, ModeOptions.BOTH):
                all_nodes.update(get_backward_nodes(node, self.num_nodes, self.vectorstore))
        return self._sort_nodes(all_nodes)

    def _sort_nodes(self, nodes: Dict[str, NodeWithScore]) -> List[NodeWithScore]:
        """
        Sort nodes by constructing a chain order.
        First, find a starting node whose previous node is not in the collected set.
        Then follow the chain via next_node pointers.
        Any nodes not reached are appended at the end.
        """
        if not nodes:
            return []

        node_map = nodes
        all_ids = set(node_map.keys())
        start = None
        for node in node_map.values():
            prev_info = node.node.prev_node
            if not prev_info or prev_info.node_id not in all_ids:
                start = node
                break
        if not start:
            start = next(iter(node_map.values()))

        sorted_nodes = [start]
        visited = {start.node.node_id}
        current = start
        while current.node.next_node and current.node.next_node.node_id in node_map:
            next_node = node_map[current.node.next_node.node_id]
            if next_node.node.node_id in visited:
                break
            sorted_nodes.append(next_node)
            visited.add(next_node.node.node_id)
            current = next_node

        # Append any remaining nodes that were not part of the main chain.
        for node in node_map.values():
            if node.node.node_id not in visited:
                sorted_nodes.append(node)
        return sorted_nodes
