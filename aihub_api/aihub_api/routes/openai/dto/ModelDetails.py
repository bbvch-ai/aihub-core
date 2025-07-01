import time
from typing import Optional

from pydantic import BaseModel, Field
from typing_extensions import Annotated


class ModelDetails(BaseModel):
    id: Annotated[str, Field(description="The ID of the model.")]

    object: Annotated[str, Field(description="The type of object.")] = "model"

    created: int = Field(
        default_factory=lambda: int(time.time()), description="The Unix timestamp of when the model was created."
    )

    owned_by: Annotated[str, Field(description="The user ID of the owner.")] = "aihub"

    agent_class: Annotated[Optional[str], Field(description="The agent class of the model.")] = None
    agent_id: Annotated[Optional[str], Field(description="The agent ID of the model.")] = None
