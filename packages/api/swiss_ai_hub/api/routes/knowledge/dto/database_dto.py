from typing import Annotated

from pydantic import BaseModel, Field

from swiss_ai_hub.api.routes.knowledge.dto.namespace_dto import NamespaceDTO


class DatabaseDTO(BaseModel):
    name: Annotated[str, Field(..., description="Name of database")]
    display_name: Annotated[str | None, Field(..., description="Localized display name of database")]
    auto_sync: Annotated[bool, Field(..., description="Whether this database auto-syncs namespaces")]
    deletable: Annotated[
        bool,
        Field(
            ...,
            description="Whether the whole database may be deleted; false for auto-synced and legacy "
            "default_rag/shared_rag databases. Namespaces inside a non-deletable database can still be deleted.",
        ),
    ]
    ingestor: Annotated[
        str,
        Field(
            ...,
            description="Identifier of the ingestion pipeline that processes this database, as served by "
            "GET /knowledge/ingestors. Visible to anyone who can see the database, so a database-level "
            "rule holder learns how it is configured without seeing its namespaces.",
        ),
    ]
    namespaces: Annotated[list[NamespaceDTO], Field(..., description="List of namespaces")]
