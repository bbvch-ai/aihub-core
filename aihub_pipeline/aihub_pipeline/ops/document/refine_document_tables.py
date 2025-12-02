from dagster import OpExecutionContext, Output, op

from aihub_pipeline.resources.parser.TableRefinementResource import TableRefinementResource
from aihub_pipeline.types.RefDocDocument import RefDocDocument


@op(code_version="v1")
def refine_document_tables(
    context: OpExecutionContext, ref_doc: RefDocDocument, table_refinement: TableRefinementResource
) -> Output[RefDocDocument]:
    """Refine tables in document using LLM to detect structure and split merged tables."""
    refined_doc = table_refinement.refine(ref_doc)
    context.log.info(f"Refined document tables: {len(ref_doc.text)} -> {len(refined_doc.text)} chars")
    return Output(
        RefDocDocument(text=refined_doc.text, extra_info=ref_doc.extra_info, metadata=ref_doc.metadata, id_=ref_doc.id_)
    )
