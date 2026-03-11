from typing import Annotated

from pydantic import BaseModel, Field

from swiss_ai_hub.core.infrastructure.mem0.types.memory_type import MemoryType
from swiss_ai_hub.core.infrastructure.mem0.types.modified_memory import ModifiedMemory
from swiss_ai_hub.core.infrastructure.mem0.types.modified_relations import ModifiedRelations


class MemoryAdded(BaseModel):
    owner_id: Annotated[str, Field(description="The user ID or tenant ID that created the memory.")]
    user_id: Annotated[str | None, Field(description="The user ID.", alias="_user_id")]
    agent_id: Annotated[str | None, Field(description="The agent ID.", alias="_agent_id")]
    thread_id: Annotated[str | None, Field(description="The thread ID.", alias="_thread_id")]
    display_id: Annotated[str | None, Field(description="The display ID.", alias="_display_id")]
    run_id: Annotated[str | None, Field(description="The run ID.", alias="_run_id")]
    type: Annotated[MemoryType, Field(description="The type of the memory.", alias="_type")]
    tenant_id: Annotated[str | None, Field(description="The tenant ID for multi-tenancy support.", alias="_tenant_id")]
    tenant_namespace: Annotated[
        str | None, Field(description="The tenant namespace for department-level scoping.", alias="_tenant_namespace")
    ]
    results: Annotated[list[ModifiedMemory], Field(description="The list of modified memories.")] = []
    relations: Annotated[ModifiedRelations, Field(description="The list of modified relations.")] = ModifiedRelations()
