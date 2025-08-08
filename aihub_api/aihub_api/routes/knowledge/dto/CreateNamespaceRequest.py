from typing import Annotated

from pydantic import BaseModel, Field


class CreateNamespaceRequest(BaseModel):
    database_name: Annotated[str, Field(description="The name of the database to which the namespace belongs.")]
    namespace_name: Annotated[str, Field(description="The name of the namespace to create.")]
    folder_name: Annotated[str, Field(description="The name of the folder to which the namespace belongs.")]
    display_name: Annotated[str, Field(description="The display name of the namespace in the user's locale.")] = None
    description: Annotated[str, Field(description="A short description of the namespace in the user's locale.")] = None
