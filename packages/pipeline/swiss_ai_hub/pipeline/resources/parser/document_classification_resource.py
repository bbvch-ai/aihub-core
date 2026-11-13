from dagster import ConfigurableResource
from llama_index.core.llms import LLM
from swiss_ai_hub.core.generative_ai import DocumentClassification, DocumentClassifier
from swiss_ai_hub.core.persistence import DOCUMENT_TITLE

from swiss_ai_hub.pipeline.types.ref_doc_document import RefDocDocument
from swiss_ai_hub.pipeline.util.async_utils import run_async


class DocumentClassificationResource(ConfigurableResource):
    """Classifies a document into the closed set of types and reads its attributes (#2346).

    Carries no model of its own, like table refinement: each knowledge database is classified with the text model it
    chose, so the caller resolves the model per run and passes it in.
    """

    def classify(self, ref_doc: RefDocDocument, llm: LLM) -> tuple[RefDocDocument, DocumentClassification]:
        """The document with its classification as metadata, and the classification, for the run's own metadata."""
        title = ref_doc.metadata.get(DOCUMENT_TITLE) or ref_doc.uri.rsplit("/", 1)[-1]
        classification = run_async(DocumentClassifier.classify(ref_doc.text, title, llm))
        return ref_doc.with_classification(classification.to_metadata()), classification
