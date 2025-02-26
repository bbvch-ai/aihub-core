from pydantic import BaseModel, Field


class ServiceDTO(BaseModel):
    name: str = Field(..., description="The name of the service.")
    description: str = Field(..., description="A description of the service.")
    icon: str = Field(..., description="The icon representing the service.")
    path: str = Field(..., description="The path under which the service is callable in the frontend.")