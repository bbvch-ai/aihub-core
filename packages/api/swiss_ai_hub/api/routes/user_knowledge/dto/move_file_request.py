from typing import Annotated

from pydantic import BaseModel, Field


class MoveFileRequest(BaseModel):
    source: Annotated[str, Field(description="The file or folder to move or rename.")]
    destination: Annotated[str, Field(description="Its new path; a rename keeps the folder and changes the name.")]
