from typing import Annotated, Any, Self

from pydantic import BaseModel, Field, model_validator

from swiss_ai_hub.core.generative_ai.document.classification.document_type import DocumentType
from swiss_ai_hub.core.generative_ai.document.classification.tests.evaluation.labelled_keys import LabelledKeys


class ClassificationCase(BaseModel):
    """One labelled document: its text, its type, and the value each attribute of that type should be stored as.

    `expected` holds stored values, not copied text: `"2025-03-14"`, not `"14. März 2025"`. A key set to None means the
    document does not state it, so storing anything is a guess. A key left out is not labelled and not measured, which
    lets a real-document label file grow attribute by attribute.
    """

    id: Annotated[str, Field(description="Unique within the sample")]
    type: Annotated[DocumentType, Field(description="The type the document is")]
    title: Annotated[str, Field(description="Title or filename the classifier is shown")]
    text: Annotated[str, Field(description="Parsed text, as ingestion would hand it to the classifier")]
    expected: Annotated[
        dict[str, Any], Field(description="Stored value per labelled value key; None where the document has none")
    ] = {}
    note: Annotated[str | None, Field(description="What the case tests, for whoever reads a failure")] = None

    @model_validator(mode="after")
    def _only_keys_of_its_type(self) -> Self:
        unknown = set(self.expected) - set(LabelledKeys.value_keys(self.type))
        if unknown:
            raise ValueError(f"case {self.id}: keys {sorted(unknown)} are not attributes of {self.type}")
        return self
