from dagster import OpExecutionContext, Output, op

from swiss_ai_hub.pipeline.resources.parser.table_refinement_resource import TableRefinementResource
from swiss_ai_hub.pipeline.types.ref_doc_document import RefDocDocument
from swiss_ai_hub.pipeline.util.model_builders import ingestor_config_for_bucket, llm_config_for_bucket
from swiss_ai_hub.pipeline.util.run_routing import bucket_from_partition_key


@op(code_version="v2")
def refine_document_tables(
    context: OpExecutionContext, ref_doc: RefDocDocument, table_refinement: TableRefinementResource
) -> Output[RefDocDocument]:
    """Refine tables with the knowledge database's own text model, if the database asks for it."""
    bucket = bucket_from_partition_key(context.partition_key)
    if not ingestor_config_for_bucket(bucket).with_table_refinement:
        context.log.info(f"Table refinement is disabled for '{bucket}'; passing the document through.")
        return Output(ref_doc)

    refined_doc = table_refinement.refine(ref_doc, llm_config_for_bucket(bucket))
    context.log.info(f"Refined document tables: {len(ref_doc.text)} -> {len(refined_doc.text)} chars")
    return Output(
        RefDocDocument(text=refined_doc.text, extra_info=ref_doc.extra_info, metadata=ref_doc.metadata, id_=ref_doc.id_)
    )
