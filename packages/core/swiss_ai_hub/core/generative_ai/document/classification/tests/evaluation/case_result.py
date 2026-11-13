from typing import Annotated, Any

from pydantic import BaseModel, Field

from swiss_ai_hub.core.generative_ai.document.classification.document_type import DocumentType
from swiss_ai_hub.core.generative_ai.document.classification.tests.evaluation.attribute_comparison import (
    AttributeComparison,
)
from swiss_ai_hub.core.generative_ai.document.classification.tests.evaluation.attribute_outcome import AttributeOutcome
from swiss_ai_hub.core.generative_ai.document.classification.tests.evaluation.classification_case import (
    ClassificationCase,
)
from swiss_ai_hub.core.generative_ai.document.classification.tests.evaluation.labelled_keys import LabelledKeys
from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import DOCUMENT_TYPE


class CaseResult(BaseModel):
    """What classification stored for one case, or why it stored nothing."""

    case: Annotated[ClassificationCase, Field(description="The labelled case")]
    metadata: Annotated[dict[str, Any], Field(description="What ingestion would store; empty when the call failed")]
    error: Annotated[str | None, Field(description="Why classification failed, as the caller would see it")] = None
    seconds: Annotated[float, Field(description="Wall-clock time of the classification call")] = 0.0

    @property
    def predicted_type(self) -> DocumentType | None:
        value = self.metadata.get(DOCUMENT_TYPE)
        return DocumentType(value) if value else None

    def outcomes(self) -> dict[str, AttributeOutcome]:
        """The outcome of every labelled key; a misclassified invoice stores nothing, so its labels count as empty."""
        raw_keys = LabelledKeys.raw_key_of_value_keys()
        return {
            key: AttributeComparison.outcome(expected, self.metadata.get(key), self.metadata.get(raw_keys[key]))
            for key, expected in self.case.expected.items()
        }
