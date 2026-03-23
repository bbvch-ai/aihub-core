from typing import Annotated

from pydantic import AliasChoices, BaseModel, Field

from swiss_ai_hub.core.infrastructure.mem0.types.memory_metadata import MemoryMetadata


class Memory(BaseModel):
    id: Annotated[str, Field(description="The unique identifier for the memory.")]
    owner_id: Annotated[
        str,
        Field(
            description="The user ID of the user who created the memory.",
            validation_alias=AliasChoices("owner_id", "user_id"),
        ),
    ]
    memory: Annotated[str, Field(description="The memory deduced from the text data.")]
    score: Annotated[float | None, Field(description="The score of the memory.")] = None
    created_at: Annotated[str, Field(description="The timestamp when the memory was created.")]
    metadata: Annotated[MemoryMetadata, Field(description="The metadata associated with the memory.")]
