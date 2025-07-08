from typing import Annotated

from pydantic import BaseModel, Field


class ServiceDTO(BaseModel):
    name: Annotated[str, Field(description="The name of the service.")]
    description: Annotated[str, Field(description="A description of the service.")]
    icon: Annotated[str, Field(description="The icon representing the service.")]
    path: Annotated[str, Field(description="The path under which the service is callable in the frontend.")]
    user_is_admin: Annotated[bool, Field(description="Whether the user is an admin of the service.")] = False
