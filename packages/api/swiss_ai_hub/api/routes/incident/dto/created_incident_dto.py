from typing import Annotated

from pydantic import BaseModel, Field


class CreatedIncidentDTO(BaseModel):
    """What the reporter is shown after submitting.

    Carries the issue number so support and reporter can name the same report, but no issue
    URL: the reporter has no GitHub account and a link they cannot open reads as a broken
    promise rather than a receipt.
    """

    number: Annotated[int, Field(description="Issue number in the incident repository")]
    reference: Annotated[str, Field(description="Reference shown to the reporter and used in attachment paths")]
    attachments: Annotated[int, Field(description="How many files were filed with the report")] = 0
