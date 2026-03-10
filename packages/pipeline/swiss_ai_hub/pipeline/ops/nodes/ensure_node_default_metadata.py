from dagster import Output, op
from llama_index.core.schema import TextNode
from swiss_ai_hub.core.generative_ai.document.types.IngestedNode import IngestedNode


@op(code_version="v1")
def ensure_node_default_metadata(nodes: list[TextNode]) -> Output[list[TextNode]]:
    """Inserts a list of nodes into the vector store by having the appropriate
    IO manager set as the output IO Manager"""
    for node in nodes:
        IngestedNode.from_llama_index_node(node)
    return Output(nodes)
