from typing import Annotated

from pydantic import BaseModel, Field


class FilePathDTO(BaseModel):
    path: Annotated[str, Field(description="The affected path, relative to the user's file space.")]
