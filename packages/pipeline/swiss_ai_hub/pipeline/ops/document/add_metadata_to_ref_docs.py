from dagster import Output, op

from swiss_ai_hub.pipeline.types.ref_doc_document import RefDocDocument
from swiss_ai_hub.pipeline.util.meta_utils import ref_doc_metadata_table


@op(code_version="v1")
def add_metadata_to_ref_docs(
    ref_docs: list[RefDocDocument],
) -> Output[list[RefDocDocument]]:
    """Adds metadata to Ref Docs and returns them."""
    return Output(
        ref_docs,
        metadata={
            "Number of Ref Docs": len(ref_docs),
            "Ref Docs Table": ref_doc_metadata_table(ref_docs),
        },
    )
