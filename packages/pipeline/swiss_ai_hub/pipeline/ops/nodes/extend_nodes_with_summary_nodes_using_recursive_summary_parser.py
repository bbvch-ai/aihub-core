from dagster import OpExecutionContext, op
from llama_index.core.schema import TextNode

from swiss_ai_hub.pipeline.resources.parser.recursive_summary_parser_resource import RecursiveSummaryParserResource
from swiss_ai_hub.pipeline.util.model_builders import (
    build_language_model,
    ingestor_config_for_bucket,
    llm_config_for_bucket,
)
from swiss_ai_hub.pipeline.util.run_routing import bucket_from_partition_key


@op(code_version="v2")
def extend_nodes_with_summary_nodes_using_recursive_summary_parser(
    context: OpExecutionContext,
    content_nodes: list[TextNode],
    summary_parser: RecursiveSummaryParserResource,
) -> list[TextNode]:
    """Summary nodes for this document, with the knowledge database's own text model — or none, if it opted out.

    An empty result is what lets the summary asset stay in every database's graph: the downstream embed and
    insert ops have nothing to do and the vector store IO manager skips an empty write.
    """
    bucket = bucket_from_partition_key(context.partition_key)
    if not ingestor_config_for_bucket(bucket).with_summary_nodes:
        context.log.info(f"Summary nodes are disabled for '{bucket}'; nothing to extend.")
        return []

    language_model = build_language_model(bucket)
    summary_parser = summary_parser.get_summary_parser(llm=language_model, llm_config=llm_config_for_bucket(bucket))
    summary_and_content_nodes = summary_parser.summarize_nodes(nodes=content_nodes)
    context.log.info(f"Extended nodes with summary nodes: {len(summary_and_content_nodes)}")
    return summary_and_content_nodes
