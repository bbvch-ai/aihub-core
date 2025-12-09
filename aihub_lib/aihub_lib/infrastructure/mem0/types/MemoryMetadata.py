from typing import Annotated

from pydantic import BaseModel, Field

from aihub_lib.infrastructure.mem0.types.MemoryType import MemoryType


class MemoryMetadata(BaseModel):
    user_id: Annotated[str | None, Field(description="The user ID.", alias="_user_id")]
    agent_id: Annotated[str | None, Field(description="The agent ID.", alias="_agent_id")]
    thread_id: Annotated[str | None, Field(description="The thread ID.", alias="_thread_id")]
    display_id: Annotated[str | None, Field(description="The display ID.", alias="_display_id")]
    run_id: Annotated[str | None, Field(description="The run ID.", alias="_run_id")]
    type: Annotated[MemoryType, Field(description="The type of the memory.", alias="_type")]
    organization_name: Annotated[
        str | None, Field(description="The organization memory database.", alias="_organization_name")
    ]
    organization_namespace: Annotated[
        str | None, Field(description="The organization memory namespace.", alias="_organization_namespace")
    ]
