import time

from pydantic import BaseModel, Field


class ModelDetails(BaseModel):
    id: str = Field(..., description="The ID of the model.")
    object: str = Field("model", description="The type of object.")
    created: int = Field(..., description="The Unix timestamp of when the model was created.", default_factory=lambda: int(time.time()))
    owned_by: str = Field("aihub", description="The user ID of the owner.")