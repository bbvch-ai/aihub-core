from dagster import DataVersion, Out, Output, op

from swiss_ai_hub.pipeline.types.RefDocDocument import RefDocDocument
from swiss_ai_hub.pipeline.util.meta_utils import ref_doc_metadata


@op(code_version="v1", out=Out(io_manager_key="doc_store_io_manager"))
def insert_ref_doc_into_docstore(ref_doc: RefDocDocument) -> Output[RefDocDocument]:
    """Inserts a RefDocDocument into the Document Store by having the appropriate
    IO manager set as the output IO Manager.
    """
    return Output(
        ref_doc,
        metadata=ref_doc_metadata(ref_doc),
        data_version=DataVersion(f"{ref_doc.updated}-{ref_doc.hash}"),
    )
