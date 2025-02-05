from typing import List

from pydantic import BaseModel, Field

from aihub_api.routes.openai.dto.ModelDetails import ModelDetails


class ModelResponse(BaseModel):
    object: str = Field("list", description="The type of object.")
    data: List[ModelDetails] = Field(..., description="The list of models.")
