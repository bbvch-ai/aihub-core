from dagster import OpExecutionContext, Output, op

from aihub_pipeline.resources.parser.TextRefinementResource import TextRefinementResource
from aihub_pipeline.types.RefDocDocument import RefDocDocument


@op(code_version="v1")
def refine_document_text(
    context: OpExecutionContext, ref_doc: RefDocDocument, text_refinement: TextRefinementResource
) -> Output[RefDocDocument]:
    """Refine document text using LLM to fix OCR errors and structural issues."""
    refined_doc = text_refinement.refine(ref_doc)
    context.log.info(f"Refined document text: {len(ref_doc.text)} -> {len(refined_doc.text)} chars")
    return Output(RefDocDocument(text=refined_doc.text, extra_info=ref_doc.extra_info, metadata=ref_doc.metadata))
