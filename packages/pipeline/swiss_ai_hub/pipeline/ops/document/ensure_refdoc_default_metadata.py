from dagster import Output, op
from swiss_ai_hub.core.generative_ai.document.types.IngestedDocument import IngestedDocument

from swiss_ai_hub.pipeline.types.RefDocDocument import RefDocDocument


@op(code_version="v1")
def ensure_refdoc_default_metadata(ref_doc: RefDocDocument) -> Output[RefDocDocument]:
    """Ensures RefDoc is compatible with InsertedDocument object from aihub-lib."""
    IngestedDocument.from_ref_doc(ref_doc)
    return Output(ref_doc)
