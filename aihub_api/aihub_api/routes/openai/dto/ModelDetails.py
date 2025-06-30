import time

from pydantic import BaseModel, Field
from typing_extensions import Annotated


class ModelDetails(BaseModel):
    id: Annotated[str, Field(description="The ID of the model.")]

    object: Annotated[str, Field(description="The type of object.")] = "model"

    created: Annotated[int, Field(description="The Unix timestamp of when the model was created.")] = int(time.time())

    owned_by: Annotated[str, Field(description="The user ID of the owner.")] = "aihub"
