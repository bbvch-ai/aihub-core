from typing import Annotated, Self

from pydantic import BaseModel, Field
from swiss_ai_hub.core.i18n import LocaleHandler

from swiss_ai_hub.agent.agents.knowledge_extraction_agent.extraction_request_answer import ExtractionRequestAnswer
from swiss_ai_hub.agent.capabilities.record_extraction.document_condition_text import DocumentConditionText
from swiss_ai_hub.agent.capabilities.record_extraction.extraction_form import FORM, ExtractionForm
from swiss_ai_hub.agent.capabilities.record_extraction.extraction_form_part import ExtractionFormPart


class ExtractionRequestParts(BaseModel):
    """The parts of a table request as the user reads them in the form: where, which documents, which rows, which
    columns, and, when the model searches for the documents (discovery), the exact and the semantic keywords that guide
    its search."""

    where: Annotated[str, Field(description="The places to read, or that every document in scope is.")]
    documents: Annotated[str, Field(description="The condition on whole documents, or that every document counts.")]
    rows: Annotated[str, Field(description="The condition on the rows, or that every row is kept.")]
    columns: Annotated[str, Field(description="The table's columns in the user's words.")]
    exact: Annotated[str | None, Field(description="Words the documents contain; None without discovery.")] = None
    semantic: Annotated[str | None, Field(description="What the documents are about; None without discovery.")] = None

    @classmethod
    def of(cls, reading: ExtractionRequestAnswer, t: LocaleHandler, keywords: bool = False) -> Self:
        return cls(
            where=", ".join(location.describe() for location in reading.locations) or t(f"{FORM}.where.everything"),
            documents=DocumentConditionText.of(reading.document_condition, reading.path_date_range, t)
            or t(f"{FORM}.documents.everything"),
            rows=reading.instructions or t(f"{FORM}.rows.everything"),
            columns=reading.fields or t(f"{FORM}.columns.unnamed"),
            exact=(reading.document_terms or t(f"{FORM}.exact.none")) if keywords else None,
            semantic=(reading.document_kind or t(f"{FORM}.semantic.none")) if keywords else None,
        )

    @staticmethod
    def named(reading: ExtractionRequestAnswer) -> dict[str, bool]:
        """Which parts the request named; a part it did not name has nothing to drop, in the dialog or typed."""
        return {
            "where": bool(reading.locations),
            "documents": bool(reading.document_condition or reading.path_date_range),
            "rows": bool(reading.instructions),
            "columns": bool(reading.fields),
            "exact": bool(reading.document_terms),
            "semantic": bool(reading.document_kind),
        }

    def lines(self, t: LocaleHandler) -> list[str]:
        return [ExtractionForm.line(key, value, t) for key, value in self.model_dump().items() if value is not None]

    def form(self, reading: ExtractionRequestAnswer, places: list[str], t: LocaleHandler) -> list[ExtractionFormPart]:
        """The form's questions; `places`: the collections and largest folders in scope, so the user can name one as
        the location."""
        named = ExtractionRequestParts.named(reading)
        where_hint = " ".join([t(f"{FORM}.where.hint_with_documents"), *places])
        parts = [
            ExtractionFormPart(key="where", value=self.where, named=named["where"], droppable=True, hint=where_hint),
            ExtractionFormPart(
                key="documents",
                value=self.documents,
                named=named["documents"],
                droppable=True,
                hint=t(f"{FORM}.documents.hint"),
            ),
            ExtractionFormPart(
                key="rows",
                value=self.rows,
                named=named["rows"],
                droppable=True,
                hint=t(f"{FORM}.rows.hint_with_documents"),
            ),
            ExtractionFormPart(
                key="columns",
                value=self.columns,
                named=named["columns"],
                droppable=False,
                hint=t(f"{FORM}.columns.hint"),
            ),
        ]
        if self.exact is not None and self.semantic is not None:
            parts += [
                ExtractionFormPart(
                    key="exact",
                    value=self.exact,
                    named=named["exact"],
                    droppable=True,
                    hint=t(f"{FORM}.exact.hint"),
                ),
                ExtractionFormPart(
                    key="semantic",
                    value=self.semantic,
                    named=named["semantic"],
                    droppable=True,
                    hint=t(f"{FORM}.semantic.hint"),
                ),
            ]
        return parts
