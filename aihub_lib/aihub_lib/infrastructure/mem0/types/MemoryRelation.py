from typing import Annotated

from pydantic import BaseModel, Field, AliasChoices


class MemoryRelation(BaseModel):
    """Represents a knowledge graph triple"""

    source: Annotated[str, Field(description="The source entity.")]
    relation: Annotated[
        str,
        Field(
            description="The relationship between the source and target entities.",
            validation_alias=AliasChoices("relationship", "relation"),
        ),
    ]
    target: Annotated[
        str, Field(description="The target entity.", validation_alias=AliasChoices("target", "destination"))
    ]
