from typing import Annotated, Self

from pydantic import BaseModel, Field
from swiss_ai_hub.core.incident import IncidentSettings, IssueFormUpload


class IncidentAttachmentsDTO(BaseModel):
    """How the reporter's file picker should be configured.

    Wording and accepted types come from the form definition, the two limits from the
    deployment — so an operator who raises `INCIDENT_MAX_ATTACHMENT_BYTES` does not also
    have to hunt down a translated string that repeats the old number.
    """

    label: Annotated[str, Field(description="Heading shown above the picker")]
    description: Annotated[str | None, Field(description="Guidance shown under the label")]
    required: Annotated[bool, Field(description="Whether at least one file must be attached")]
    accept: Annotated[list[str], Field(description="Accepted extensions, each with its leading dot")]
    max_files: Annotated[int, Field(description="How many files one report may carry")]
    max_bytes: Annotated[int, Field(description="Largest single attachment accepted, in bytes")]

    @classmethod
    def from_upload(
        cls,
        upload: Annotated[IssueFormUpload, "Attachment field from the definition"],
        settings: Annotated[IncidentSettings, "Deployment's incident configuration"],
    ) -> Self:
        return cls(
            label=upload.label,
            description=upload.description,
            required=upload.required,
            accept=upload.accept,
            max_files=settings.MAX_ATTACHMENTS,
            max_bytes=settings.MAX_ATTACHMENT_BYTES,
        )
