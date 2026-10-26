from typing import Annotated, Self

from pydantic import Field, model_validator
from swiss_ai_hub.core.generative_ai import KnowledgeDocumentCriteria

from swiss_ai_hub.agent.capabilities.record_extraction.extract_records_arguments import ExtractRecordsArguments


class ExtractRecordsToolArguments(ExtractRecordsArguments):
    """What a model passes to `extract_records`: a new extraction, or the next part of the one the conversation left
    pending. A separate model, so the selection preview and the blueprint's structured selection keep their fields."""

    any_of: Annotated[
        list[KnowledgeDocumentCriteria],
        Field(
            description=f"{ExtractRecordsArguments.model_fields['any_of'].description} Required for a new extraction."
        ),
    ] = []
    fields: Annotated[
        str,
        Field(
            description=f"{ExtractRecordsArguments.model_fields['fields'].description} Required for a new extraction."
        ),
    ] = ""
    continue_pending: Annotated[
        bool,
        Field(
            description="True to extract the next part of the extraction this conversation left pending, after the "
            "user agreed to continue; the other arguments are then ignored. False for a new extraction."
        ),
    ] = False

    @model_validator(mode="after")
    def _a_new_extraction_names_its_documents_and_columns(self) -> Self:
        if not self.continue_pending and not (self.any_of and self.fields.strip()):
            raise ValueError("a new extraction needs any_of and fields; to go on with a pending one, continue_pending")
        return self
