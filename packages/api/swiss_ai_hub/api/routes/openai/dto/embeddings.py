from typing import Annotated

from pydantic import BaseModel, Field


class Embeddings(BaseModel):
    object: Annotated[str, Field(description="The type of object.")] = "embedding"
    embedding: Annotated[
        list[float] | str,
        Field(description="The embedding vector, or the vector's float32 bytes as base64 when requested so."),
    ]
    index: Annotated[int, Field(description="The index of the embedding.")]
