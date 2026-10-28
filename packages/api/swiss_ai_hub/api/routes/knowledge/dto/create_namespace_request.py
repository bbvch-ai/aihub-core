from typing import Annotated

from pydantic import BaseModel, Field


class CreateNamespaceRequest(BaseModel):
    folder_name: Annotated[
        str, Field(description="The name of the folder to which the namespace belongs.", max_length=100)
    ]
    display_name: Annotated[
        str | None, Field(description="The display name of the namespace in the user's locale.", max_length=120)
    ] = None
    description: Annotated[
        str | None, Field(description="A short description of the namespace in the user's locale.", max_length=500)
    ] = None
