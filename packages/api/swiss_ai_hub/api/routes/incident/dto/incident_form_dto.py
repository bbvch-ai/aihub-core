from typing import Annotated, Any, Self

from pydantic import BaseModel, Field
from swiss_ai_hub.core.form import ALL_FORM_OPTIONS
from swiss_ai_hub.core.incident import IncidentContext, IncidentSettings, IssueForm

from swiss_ai_hub.api.routes.incident.dto.incident_attachments_dto import IncidentAttachmentsDTO


class IncidentFormDTO(BaseModel):
    """The report form, already carrying what the platform knows about this reporter."""

    elements: Annotated[
        list[ALL_FORM_OPTIONS], Field(description="Form elements to render, with known values prefilled")
    ]
    submission_specs: Annotated[
        dict[str, Any], Field(description="JSON Schema a submission to this form is validated against")
    ]
    attachments: Annotated[
        IncidentAttachmentsDTO | None,
        Field(description="Picker configuration, when the definition declares an upload field"),
    ] = None

    @classmethod
    def from_form(
        cls,
        form: Annotated[IssueForm, "Parsed form"],
        context: Annotated[IncidentContext, "What the platform knows"],
        settings: Annotated[IncidentSettings, "Deployment's incident configuration"],
    ) -> Self:
        prefilled = form.with_prefill(context.as_prefill())
        return cls(
            elements=prefilled.elements,
            submission_specs=form.submission_model().model_json_schema(),
            attachments=IncidentAttachmentsDTO.from_upload(form.upload, settings) if form.upload else None,
        )
