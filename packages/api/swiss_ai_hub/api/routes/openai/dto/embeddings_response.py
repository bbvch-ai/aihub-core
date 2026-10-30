from typing import Annotated

from openai.types.create_embedding_response import Usage
from pydantic import BaseModel, Field

from swiss_ai_hub.api.routes.openai.dto.embeddings import Embeddings


class EmbeddingsResponse(BaseModel):
    object: Annotated[str, Field(description="The type of object.")] = "list"
    model: Annotated[str, Field(description="The model name.")]
    data: Annotated[list[Embeddings], Field(description="The list of embeddings.")]
    usage: Annotated[Usage | None, Field(description="Tokens the request used.")] = None
