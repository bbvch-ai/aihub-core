from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class AnalyzerSpan(BaseModel):
    """One detection the analyzer returned: where it is in the text and of which type."""

    model_config = ConfigDict(extra="ignore")

    entity_type: Annotated[str, Field(description="The detected type, e.g. PERSON or IBAN_CODE.")]
    start: Annotated[int, Field(description="Offset of the first character.")]
    end: Annotated[int, Field(description="Offset after the last character.")]
    score: Annotated[float, Field(description="The recognizer's confidence.")] = 0.0
