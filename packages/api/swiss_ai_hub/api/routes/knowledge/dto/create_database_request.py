from typing import Annotated, Any

from pydantic import BaseModel, Field
from swiss_ai_hub.core.persistence.rag.datalake.entities import IngestorType


class CreateDatabaseRequest(BaseModel):
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
    ] = IngestorType.DOCUMENT_INGESTION.value
    configuration: Annotated[
        dict[str, Any],
        Field(
            description=(
                "The database's configuration as submitted through the ingestor's announced form: its multilingual "
                "name and description plus every knob the pipeline declares. Validated against the ingestor's schema."
            )
        ),
    ] = {}
    source: Annotated[
        str | None,
        Field(
            description=(
                "The deployed source pipeline that fills this database's data lake, as served by "
                "GET /knowledge/source-pipelines. Omit for manual upload."
            )
        ),
    ] = None
    source_configuration: Annotated[
        dict[str, Any],
        Field(
            description=(
                "The source's settings as submitted through its announced form (backend, credentials, root folder, "
                "patterns). Validated against the source's schema; secret fields are stored encrypted."
            )
        ),
    ] = {}
