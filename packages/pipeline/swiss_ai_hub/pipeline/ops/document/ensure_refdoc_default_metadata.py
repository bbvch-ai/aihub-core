from dagster import Output, op
from swiss_ai_hub.core.generative_ai.document.types.ingested_document import IngestedDocument

from swiss_ai_hub.pipeline.types.ref_doc_document import RefDocDocument


@op(code_version="v1")
def ensure_refdoc_default_metadata(ref_doc: RefDocDocument) -> Output[RefDocDocument]:
    """Ensures RefDoc is compatible with IngestedDocument from swiss-ai-hub-core."""
    IngestedDocument.from_ref_doc(ref_doc)
    return Output(ref_doc)
