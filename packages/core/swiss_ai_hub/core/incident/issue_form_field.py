from typing import Annotated, Literal

from pydantic import BaseModel, Field

IssueFormFieldType = Literal["input", "textarea", "dropdown", "checkboxes"]


class IssueFormField(BaseModel):
    """One answerable question from the issue-form definition.

    The rendered elements carry what the browser needs; this carries what the API
    needs afterwards — which label to write above the answer in the issue body,
    whether an answer was required, and which values a dropdown accepts.
    """

    id: Annotated[str, Field(description="Stable identifier, also the prefill key")]
    label: Annotated[str, Field(description="Heading written above the answer in the issue body")]
    type: Annotated[IssueFormFieldType, Field(description="Question type from the definition")]
    required: Annotated[bool, Field(description="Whether an answer must be present")] = False
    options: Annotated[list[str], Field(description="Accepted values, for dropdowns")] = []
    multiple: Annotated[bool, Field(description="Whether a dropdown accepts several values")] = False
    render: Annotated[
        str | None,
        Field(description="Language for the code fence GitHub wraps a textarea answer in, when the form asks for one"),
    ] = None
