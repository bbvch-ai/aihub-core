from typing import Annotated, Literal

from pydantic import BaseModel, Field


class HITLTopicDTO(BaseModel):
    """Topic information for routing the HITL response."""

    event_name: Annotated[str | None, Field(description="Expected response event name")] = None
    display_id: Annotated[str | None, Field(description="Display ID for the response")] = None
    thread_id: Annotated[str | None, Field(description="Thread ID")] = None
    run_id: Annotated[str | None, Field(description="Run ID")] = None
    agent_class: Annotated[str | None, Field(description="Agent class")] = None
    agent_id: Annotated[str | None, Field(description="Agent ID")] = None


class PendingHITLRequestDTO(BaseModel):
    """A pending Human-In-The-Loop request awaiting a response."""

    event_id: Annotated[str, Field(description="Unique identifier for this HITL request event")]
    message: Annotated[str, Field(description="The message or prompt presented to the human operator")]
    hitl_type: Annotated[
        Literal["input", "confirmation", "chat"],
        Field(description="Type of HITL interaction: 'input' for free-form text, 'confirmation' for yes/no, 'chat' for normal chat flow"),
    ]
    topic: Annotated[HITLTopicDTO, Field(description="Topic information for routing the response")]
    created_at: Annotated[int, Field(description="Timestamp when the request was created (microseconds since epoch)")]
