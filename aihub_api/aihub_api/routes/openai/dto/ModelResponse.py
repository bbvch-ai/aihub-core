from typing import Annotated

from pydantic import BaseModel, Field

from aihub_api.routes.openai.dto.ModelDetails import ModelDetails


class ModelResponse(BaseModel):
    object: Annotated[str, Field(description="The type of object.")] = "list"
    data: Annotated[list[ModelDetails], Field(description="The list of models.")]
