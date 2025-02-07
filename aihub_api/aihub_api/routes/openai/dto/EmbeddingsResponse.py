from typing import List

from pydantic import BaseModel, Field
from typing_extensions import Annotated

from aihub_api.routes.openai.dto.Embeddings import Embeddings


class EmbeddingsResponse(BaseModel):
    object: Annotated[str, Field(description="The type of object.")] = "list"
    model: Annotated[str, Field(description="The model name.")]
    data: Annotated[List[Embeddings], Field(description="The list of embeddings.")]
