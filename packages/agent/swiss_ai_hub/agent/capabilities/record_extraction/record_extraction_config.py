from typing import Annotated, Self

from pydantic import Field
from swiss_ai_hub.core.form import InputNumber, ModelSelect
from swiss_ai_hub.core.form.constraints import Ge, Le
from swiss_ai_hub.core.form.form import Form

from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString


class RecordExtractionConfig(Form):
    """How tables are extracted from knowledge documents: with which model, and within which limits.

    One answer extracts every document of a selection, so the ceiling bounds its time and cost: every file is one or
    more model calls. Nothing is cut: a selection above the ceiling is not extracted, the user is asked to narrow it,
    and every row goes into the table's file.
    """

    extraction_model_name: Annotated[
        str | ModelSelect | None,
        Field(description="Model that reads each document and extracts its rows; the main model when empty."),
    ] = None
    max_documents_total: Annotated[
        int | InputNumber,
        Field(description="Above this many matching documents the user is only asked to narrow the request."),
        Ge(1),
        Le(10_000),
    ] = 1000
    max_document_chars: Annotated[
        int | InputNumber,
        Field(description="Longer documents are read only in their relevant parts and marked as partly read."),
        Ge(1000),
        Le(2_000_000),
    ] = 500_000
    max_parallel_extractions: Annotated[
        int | InputNumber,
        Field(description="How many extraction calls to the model one agent replica makes at once."),
        Ge(1),
        Le(32),
    ] = 4

    @classmethod
    def as_form(cls) -> Self:
        return cls(
            extraction_model_name=ModelSelect(
                label=cls._text("extraction_model_name.label"),
                help=cls._text("extraction_model_name.help"),
                mode="chat",
            ),
            max_documents_total=InputNumber(
                label=cls._text("max_documents_total.label"),
                help=cls._text("max_documents_total.help"),
                min=1,
                max=10_000,
                step=100,
            ),
            max_document_chars=InputNumber(
                label=cls._text("max_document_chars.label"),
                help=cls._text("max_document_chars.help"),
                min=1000,
                max=2_000_000,
                step=10_000,
            ),
            max_parallel_extractions=InputNumber(
                label=cls._text("max_parallel_extractions.label"),
                help=cls._text("max_parallel_extractions.help"),
                min=1,
                max=32,
            ),
        )

    @staticmethod
    def _text(key: str) -> AgentLocaleString:
        return AgentLocaleString.from_i18n_path(f"agent.record_extraction.config.{key}")
