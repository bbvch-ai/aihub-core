from typing import List

from pydantic import BaseModel, Field
from typing_extensions import Annotated


class Embeddings(BaseModel):
    object: Annotated[str, Field(description="The type of object.")] = "embeddings"
    embedding: Annotated[List[float], Field(description="The list of embeddings.")]
    index: Annotated[int, Field(description="The index of the embedding.")]
