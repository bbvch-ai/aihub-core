from typing import Annotated

from llama_index.core.llms import LLM

from swiss_ai_hub.core.generative_ai.document.classification.document_classification import DocumentClassification
from swiss_ai_hub.core.generative_ai.document.classification.document_classification_answer import (
    DocumentClassificationAnswer,
)
from swiss_ai_hub.core.generative_ai.document.classification.document_classification_prompt import (
    DocumentClassificationPrompt,
)
from swiss_ai_hub.core.generative_ai.document.classification.document_opening_text import DocumentOpeningText
from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn


class DocumentClassifier:
    """Classifies a document into the closed set and reads its attributes, with one model call on its opening and end.

    The model only copies; `DocumentClassification.from_answer` checks every copy against the whole text and reads it.
    Takes the model as an argument and reads no configuration, so ingestion passes the knowledge database's own text
    model. Malformed output raises after the model's own retries, for the caller to decide whether that fails its work.
    """

    @staticmethod
    @trace_fn
    async def classify(
        text: Annotated[str, "The document's whole parsed text"],
        title: Annotated[str, "The document's title or filename"],
        llm: Annotated[LLM, "Model that classifies; the caller pins it to a deterministic temperature"],
    ) -> DocumentClassification:
        answer = await llm.astructured_predict(
            DocumentClassificationAnswer,
            DocumentClassificationPrompt.template(),
            **DocumentClassificationPrompt.arguments(title, DocumentOpeningText.of(text)),
        )
        return DocumentClassification.from_answer(answer, text)
