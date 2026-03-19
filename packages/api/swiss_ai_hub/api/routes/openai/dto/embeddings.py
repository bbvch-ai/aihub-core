from typing import Annotated

from pydantic import BaseModel, Field


class Embeddings(BaseModel):
    object: Annotated[str, Field(description="The type of object.")] = "embeddings"
    embedding: Annotated[list[float], Field(description="The list of embeddings.")]
    index: Annotated[int, Field(description="The index of the embedding.")]
