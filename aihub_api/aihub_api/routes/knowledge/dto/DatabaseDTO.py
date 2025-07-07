from typing import Annotated

from aihub_lib.persistence.rag.documents.entities.types.Namespace import Namespace
from pydantic import BaseModel, Field


class DatabaseDTO(BaseModel):
    name: Annotated[str, Field(..., description="Name of database")]
    namespaces: Annotated[list[Namespace], Field(..., description="List of namespaces")]
