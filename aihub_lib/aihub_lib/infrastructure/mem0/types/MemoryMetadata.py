from typing import Annotated

from pydantic import AliasChoices, BaseModel, Field

from aihub_lib.infrastructure.mem0.types.MemoryType import MemoryType


class MemoryMetadata(BaseModel):
    user_id: Annotated[
        str,
        Field(description="The user ID.", validation_alias=AliasChoices("user_id", "_user_id")),
    ]
    agent_id: Annotated[
        str,
        Field(description="The agent ID.", validation_alias=AliasChoices("agent_id", "_agent_id")),
    ]
    thread_id: Annotated[
        str,
        Field(description="The thread ID.", validation_alias=AliasChoices("thread_id", "_thread_id")),
    ]
    display_id: Annotated[
        str,
        Field(description="The display ID.", validation_alias=AliasChoices("display_id", "_display_id")),
    ]
    run_id: Annotated[
        str,
        Field(description="The run ID.", validation_alias=AliasChoices("run_id", "_run_id")),
    ]
    type: Annotated[
        MemoryType,
        Field(description="The type of the memory.", validation_alias=AliasChoices("type", "_type")),
    ]
    organization_name: Annotated[
        str | None,
        Field(
            description="The organization memory database.",
            validation_alias=AliasChoices("organization_name", "_organization_name"),
        ),
    ] = None
    organization_namespace: Annotated[
        str | None,
        Field(
            description="The organization memory namespace.",
            validation_alias=AliasChoices("organization_namespace", "_organization_namespace"),
        ),
    ] = None
