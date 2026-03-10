from dagster import OpExecutionContext, ResourceParam, op
from llama_index.core.llms import LLM
from llama_index.core.schema import TextNode

from swiss_ai_hub.pipeline.resources.parser.RecursiveSummaryParserResource import RecursiveSummaryParserResource


@op(code_version="v1")
def extend_nodes_with_summary_nodes_using_recursive_summary_parser(
    context: OpExecutionContext,
    content_nodes: list[TextNode],
    language_model: ResourceParam[LLM],
    summary_parser: RecursiveSummaryParserResource,
) -> list[TextNode]:
    summary_parser = summary_parser.get_summary_parser(llm=language_model)
    summary_and_content_nodes = summary_parser.summarize_nodes(nodes=content_nodes)
    context.log.info(f"Extended nodes with summary nodes: {len(summary_and_content_nodes)}")
    return summary_and_content_nodes
