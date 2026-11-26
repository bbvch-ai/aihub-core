from datetime import datetime
from typing import Annotated, Any

from pydantic import BaseModel, Field

from swiss_ai_hub.api.routes.knowledge.dto.namespace_dto import NamespaceDTO


class DatabaseDTO(BaseModel):
    name: Annotated[str, Field(..., description="Name of database")]
    display_name: Annotated[str | None, Field(..., description="Localized display name of database")]
    source: Annotated[
        str | None,
        Field(
            ...,
            description="Identifier of the source pipeline that fills this database, as served by "
            "GET /knowledge/source-pipelines; null when documents are uploaded by hand. A sourced database "
            "accepts no manual uploads and generates its namespaces from the source's folders.",
        ),
    ]
    source_configuration: Annotated[
        dict[str, Any],
        Field(
            default_factory=dict,
            description="The source's settings for this database, secret fields masked; empty for manual upload.",
        ),
    ]
    deletable: Annotated[
        bool,
        Field(
            ...,
            description="Whether the database itself may be deleted; false for the legacy default_rag/shared_rag "
            "databases, which are re-provisioned from deployment configuration. Namespaces and individual "
            "documents are governed separately.",
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
    classification_available: Annotated[
        bool,
        Field(
            description="Whether the documents of this database can be classified (#2346): false for a legacy or "
            "unassigned pipeline, and for a database whose configuration switched classification off.",
        ),
    ] = False
    classification_requested_at: Annotated[
        datetime | None,
        Field(
            description="When classification of the documents already ingested was requested (UTC); null when none "
            "is pending. Cleared by the pipeline once its backfill ran.",
        ),
    ] = None
    classification_failed_at: Annotated[
        datetime | None,
        Field(
            description="The request (UTC) the pipeline gave up on after its backfill runs kept failing; null when the "
            "last request did not fail. Cleared by a new request.",
        ),
    ] = None
    namespaces: Annotated[list[NamespaceDTO], Field(..., description="List of namespaces")]
