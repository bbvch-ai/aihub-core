from typing import Annotated

from pydantic import BaseModel, Field


class NamespaceResponse(BaseModel):
    id: Annotated[str, Field(description="The unique identifier for the namespace.")]
    bucket_id: Annotated[str, Field(description="The ID of the parent bucket containing the namespace.")]
    namespace_name: Annotated[str, Field(description="The name of the namespace.")]
    folder_name: Annotated[
        str,
        Field(description="The corresponding folder name in the data storage."),
    ]
    display_name: Annotated[str | None, Field(description="A user-friendly display name for the namespace.")] = None
    description: Annotated[str | None, Field(description="A brief description of the namespace's contents.")] = None
