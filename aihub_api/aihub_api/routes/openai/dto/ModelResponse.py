from typing import List

from pydantic import BaseModel, Field
from typing_extensions import Annotated

from aihub_api.routes.openai.dto.ModelDetails import ModelDetails


class ModelResponse(BaseModel):
    object: Annotated[str, Field(description="The type of object.")] = "list"
    data: Annotated[List[ModelDetails], Field(description="The list of models.")]
