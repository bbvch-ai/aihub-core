from typing import List

from llama_index.core.schema import NodeWithScore
from llama_index.core.vector_stores.types import BasePydanticVectorStore

from aihub_lib.generative_ai.processors.ParentSummaryPostProcessor import ParentSummaryPostProcessor


def retrieve_parent_summary_nodes(
    vector_store: BasePydanticVectorStore,
    nodes: List[NodeWithScore],
    max_levels: int = 1,
) -> List[NodeWithScore]:
    parent_summary_postprocessor = ParentSummaryPostProcessor(
        vectorstore=vector_store,
        max_levels=max_levels,
    )
    nodes = parent_summary_postprocessor.postprocess_nodes(nodes)
    return nodes
