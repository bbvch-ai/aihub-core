from typing import Annotated

from pydantic import BaseModel, Field

from aihub_api.routes.knowledge.dto.NamespaceDTO import NamespaceDTO


class DatabaseDTO(BaseModel):
    name: Annotated[str, Field(..., description="Name of database")]
    namespaces: Annotated[list[NamespaceDTO], Field(..., description="List of namespaces")]
