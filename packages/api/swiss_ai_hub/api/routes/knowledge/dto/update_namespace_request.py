from typing import Annotated

from pydantic import BaseModel, Field


class UpdateNamespaceRequest(BaseModel):
    display_name: Annotated[str | None, Field(description="The new display name for the namespace.")] = None
    description: Annotated[str | None, Field(description="The new description of the namespace's contents.")] = None
