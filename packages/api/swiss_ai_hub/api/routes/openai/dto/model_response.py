from typing import Annotated

from pydantic import BaseModel, Field

from swiss_ai_hub.api.routes.openai.dto.model_details import ModelDetails


class ModelResponse(BaseModel):
    object: Annotated[str, Field(description="The type of object.")] = "list"
    data: Annotated[list[ModelDetails], Field(description="The list of models.")]
