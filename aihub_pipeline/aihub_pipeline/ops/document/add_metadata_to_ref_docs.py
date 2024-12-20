from typing import List

from dagster import Output, op

from aihub_pipeline.types.RefDocDocument import RefDocDocument
from aihub_pipeline.util.meta_utils import ref_doc_metadata_table


@op(code_version="v1")
def add_metadata_to_ref_docs(
    ref_docs: List[RefDocDocument],
) -> Output[List[RefDocDocument]]:
    """Adds metadata to Ref Docs and returns them."""
    return Output(
        ref_docs,
        metadata={
            "Number of Ref Docs": len(ref_docs),
            "Ref Docs Table": ref_doc_metadata_table(ref_docs),
        },
    )
