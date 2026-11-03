from typing import Annotated, Self

from pydantic import BaseModel, Field
from swiss_ai_hub.core.i18n import LocaleHandler

from swiss_ai_hub.agent.agents.knowledge_extraction_agent.extraction_request_answer import ExtractionRequestAnswer
from swiss_ai_hub.agent.capabilities.record_extraction.extraction_form import FORM, ExtractionForm
from swiss_ai_hub.agent.capabilities.record_extraction.extraction_form_part import ExtractionFormPart


class ExtractionRequestParts(BaseModel):
    """The parts of a table request as the user reads them in the form: where, which rows, which columns, and, when the
    model searches for the documents (discovery), the exact and the semantic keywords that guide its search."""

    where: Annotated[str, Field(description="The places to read, or that every document in scope is.")]
    rows: Annotated[str, Field(description="The condition on the rows, or that every row is kept.")]
    columns: Annotated[str, Field(description="The table's columns in the user's words.")]
    exact: Annotated[str | None, Field(description="Words the documents contain; None without discovery.")] = None
    semantic: Annotated[str | None, Field(description="What the documents are about; None without discovery.")] = None

    @classmethod
    def of(cls, reading: ExtractionRequestAnswer, t: LocaleHandler, keywords: bool = False) -> Self:
        return cls(
            where=", ".join(location.describe() for location in reading.locations) or t(f"{FORM}.where.everything"),
            rows=reading.instructions or t(f"{FORM}.rows.everything"),
            columns=reading.fields or t(f"{FORM}.columns.unnamed"),
            exact=(reading.document_terms or t(f"{FORM}.exact.none")) if keywords else None,
            semantic=(reading.document_kind or t(f"{FORM}.semantic.none")) if keywords else None,
        )

    def lines(self, t: LocaleHandler) -> list[str]:
        return [ExtractionForm.line(key, value, t) for key, value in self.model_dump().items() if value is not None]

    def form(self, reading: ExtractionRequestAnswer, folders: str, t: LocaleHandler) -> list[ExtractionFormPart]:
        """The form's questions; `folders`: the largest folders in scope, so the user can name one as the location."""
        where_hint = t(f"{FORM}.where.hint")
        if folders:
            where_hint = f"{where_hint} {t(f'{FORM}.where.folders', folders=folders)}"
        parts = [
            ExtractionFormPart(
                key="where", value=self.where, named=bool(reading.locations), droppable=True, hint=where_hint
            ),
            ExtractionFormPart(
                key="rows",
                value=self.rows,
                named=bool(reading.instructions),
                droppable=True,
                hint=t(f"{FORM}.rows.hint"),
            ),
            ExtractionFormPart(
                key="columns",
                value=self.columns,
                named=bool(reading.fields),
                droppable=False,
                hint=t(f"{FORM}.columns.hint"),
            ),
        ]
        if self.exact is not None and self.semantic is not None:
            parts += [
                ExtractionFormPart(
                    key="exact",
                    value=self.exact,
                    named=bool(reading.document_terms),
                    droppable=True,
                    hint=t(f"{FORM}.exact.hint"),
                ),
                ExtractionFormPart(
                    key="semantic",
                    value=self.semantic,
                    named=bool(reading.document_kind),
                    droppable=True,
                    hint=t(f"{FORM}.semantic.hint"),
                ),
            ]
        return parts
