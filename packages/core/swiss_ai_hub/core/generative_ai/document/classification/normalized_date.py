from datetime import date
from typing import Annotated, Self

from pydantic import BaseModel, Field, model_validator

from swiss_ai_hub.core.generative_ai.document.classification.date_precision import DatePrecision


class NormalizedDate(BaseModel):
    """A date or period read from document text, as the first and last day it covers.

    One shape for both: "14. März 2025" covers one day, "März 2025" the whole month, so a range filter on the start
    and end compares like with like whatever the document wrote.
    """

    start: Annotated[date, Field(description="First day covered")]
    end: Annotated[date, Field(description="Last day covered")]
    precision: Annotated[DatePrecision, Field(description="How much of the date the text states")]

    @model_validator(mode="after")
    def _start_not_after_end(self) -> Self:
        if self.start > self.end:
            raise ValueError(f"start {self.start} is after end {self.end}")
        return self
