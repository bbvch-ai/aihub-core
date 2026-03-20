from typing import Annotated

from pydantic import BaseModel, Field


class SubmittedFormDTO(BaseModel):
    process_class: Annotated[str, Field(description="The processes class identifier.")]
    process_id: Annotated[str, Field(description="Unique identifier for the specific process instance.")]

    process_walkthrough_id: Annotated[
        str, Field(description="Unique identifier for this specific process walk through.")
    ]
