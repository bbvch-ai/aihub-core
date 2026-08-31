from typing import Annotated

from pydantic import BaseModel, Field
from swiss_ai_hub.core.persistence.rag.datalake.entities import IngestorType


class CreateDatabaseRequest(BaseModel):
    display_name: Annotated[
        str | None, Field(description="The display name of the knowledge database in the user's locale.")
    ] = None
    description: Annotated[
        str | None, Field(description="A short description of the knowledge database in the user's locale.")
    ] = None
    # A plain str, not IngestorType: a deployment's own pipeline must be representable on the wire.
    # See ADR 2026_06_18_rag_pipeline_route_per_run.
    ingestor: Annotated[
        str,
        Field(
            description=(
                "The deployed ingestion pipeline that processes this database's documents. "
                "Valid values are served by GET /knowledge/ingestors."
            )
        ),
    ] = IngestorType.RAG.value
