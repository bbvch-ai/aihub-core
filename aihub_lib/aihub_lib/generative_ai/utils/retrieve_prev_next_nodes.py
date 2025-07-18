from llama_index.core.schema import NodeWithScore
from llama_index.core.vector_stores.types import BasePydanticVectorStore

from aihub_lib.generative_ai.processors.VectorPrevNextPostProcessor import ModeOptions, VectorPrevNextPostProcessor


def retrieve_prev_next_nodes(
    vector_store: BasePydanticVectorStore, num_nodes: int, prev_next_mode: ModeOptions, nodes: list[NodeWithScore]
) -> list[NodeWithScore]:
    prev_next_postprocessor = VectorPrevNextPostProcessor(
        vectorstore=vector_store,
        num_nodes=num_nodes,
        mode=prev_next_mode,
    )
    nodes = prev_next_postprocessor.postprocess_nodes(nodes)
    return nodes
