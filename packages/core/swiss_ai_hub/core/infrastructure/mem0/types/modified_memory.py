from typing import Annotated

from pydantic import BaseModel, Field

from swiss_ai_hub.core.infrastructure.mem0.types.memory_event_type import MemoryEventType


class ModifiedMemory(BaseModel):
    id: Annotated[str, Field(description="The unique identifier for the memory.")]
    memory: Annotated[str, Field(description="The memory deduced from the text data.")]
    event: Annotated[MemoryEventType, Field(description="The type of event that occurred.")]
    previous_memory: Annotated[str | None, Field(description="The previous memory value.")] = None
