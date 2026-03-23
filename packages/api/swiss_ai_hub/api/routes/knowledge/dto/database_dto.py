from typing import Annotated

from pydantic import BaseModel, Field

from swiss_ai_hub.api.routes.knowledge.dto.namespace_dto import NamespaceDTO


class DatabaseDTO(BaseModel):
    name: Annotated[str, Field(..., description="Name of database")]
    display_name: Annotated[str | None, Field(..., description="Localized display name of database")]
    auto_sync: Annotated[bool, Field(..., description="Whether this database auto-syncs namespaces")]
    namespaces: Annotated[list[NamespaceDTO], Field(..., description="List of namespaces")]
