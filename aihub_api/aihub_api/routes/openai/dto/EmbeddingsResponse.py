from typing import List

from pydantic import BaseModel, Field

from aihub_api.routes.openai.dto.Embeddings import Embeddings


class EmbeddingsResponse(BaseModel):
    object: str = Field("list", description="The type of object.")
    model: str = Field(..., description="The model name.")
    data: List[Embeddings] = Field(..., description="The list of embeddings.")
