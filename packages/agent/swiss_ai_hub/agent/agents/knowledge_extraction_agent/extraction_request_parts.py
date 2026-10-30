from typing import Annotated, Self

from pydantic import BaseModel, Field
from swiss_ai_hub.core.i18n import LocaleHandler

from swiss_ai_hub.agent.agents.knowledge_extraction_agent.extraction_request_answer import ExtractionRequestAnswer

_FORM = "agent.knowledge_extraction_agent.form"


class ExtractionRequestParts(BaseModel):
    """The three parts of a table request as the user reads them in the form: where, which rows, which columns."""

    where: Annotated[str, Field(description="The places to read, or that every document in scope is.")]
    rows: Annotated[str, Field(description="The condition on the rows, or that every row is kept.")]
    columns: Annotated[str, Field(description="The table's columns in the user's words.")]

    @classmethod
    def of(cls, reading: ExtractionRequestAnswer, t: LocaleHandler) -> Self:
        return cls(
            where=", ".join(location.describe() for location in reading.locations) or t(f"{_FORM}.where.everything"),
            rows=reading.instructions or t(f"{_FORM}.rows.everything"),
            columns=reading.fields or t(f"{_FORM}.columns.unnamed"),
        )

    def lines(self, t: LocaleHandler) -> list[str]:
        return [t(f"{_FORM}.{key}.line", value=value) for key, value in self.model_dump().items()]
