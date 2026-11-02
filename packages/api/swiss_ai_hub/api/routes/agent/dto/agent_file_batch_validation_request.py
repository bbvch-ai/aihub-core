from typing import Annotated

from pydantic import BaseModel, Field

from swiss_ai_hub.api.routes.agent.dto.agent_file_validation_item import AgentFileValidationItem


class AgentFileBatchValidationRequest(BaseModel):
    """All files of one chat turn, checked together so a turn costs one call and places its files once."""

    thread_id: Annotated[
        str | None,
        Field(
            pattern=r"^[0-9a-f]{24}$",
            description="The conversation the files are attached in; once none is missing, they are also placed in "
            "the user's files there.",
        ),
    ] = None
    files: Annotated[
        list[AgentFileValidationItem],
        Field(min_length=1, max_length=1000, description="The uploaded files to check."),
    ]
