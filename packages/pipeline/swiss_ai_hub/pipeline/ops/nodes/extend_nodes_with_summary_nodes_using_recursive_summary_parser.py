from dagster import OpExecutionContext, op
from llama_index.core.schema import TextNode

from swiss_ai_hub.pipeline.resources.parser.recursive_summary_parser_resource import RecursiveSummaryParserResource
from swiss_ai_hub.pipeline.util.model_builders import build_language_model
from swiss_ai_hub.pipeline.util.run_routing import bucket_from_partition_key


@op(code_version="v1")
def extend_nodes_with_summary_nodes_using_recursive_summary_parser(
    context: OpExecutionContext,
    content_nodes: list[TextNode],
    summary_parser: RecursiveSummaryParserResource,
) -> list[TextNode]:
    language_model = build_language_model(bucket_from_partition_key(context.partition_key))
    summary_parser = summary_parser.get_summary_parser(llm=language_model)
    summary_and_content_nodes = summary_parser.summarize_nodes(nodes=content_nodes)
    context.log.info(f"Extended nodes with summary nodes: {len(summary_and_content_nodes)}")
    return summary_and_content_nodes
