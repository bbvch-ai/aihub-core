from typing import List

from pydantic import BaseModel, Field


class Embeddings(BaseModel):
    object: str = Field("embeddings", description="The type of object.")
    embedding: List[List[float]] = Field(..., description="The list of embeddings.")
    index: int = Field(..., description="The index of the embedding.")