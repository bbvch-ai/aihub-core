from typing import Annotated

from pydantic import BaseModel, Field


class CreateFolderRequest(BaseModel):
    path: Annotated[str, Field(description="The new folder's path in the user's file space.")]
