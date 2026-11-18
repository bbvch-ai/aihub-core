from datetime import datetime
from typing import Annotated, Any

from pydantic import BaseModel, Field


class DatabaseResponse(BaseModel):
    name: Annotated[str, Field(description="The database name (also the Milvus collection and Mongo store name).")]
    bucket_name: Annotated[str, Field(description="The S3 bucket / data lake container name.")]
    ingestor: Annotated[str, Field(description="The deployed ingestion pipeline that owns this database.")]
    configuration: Annotated[
        dict[str, Any],
        Field(
            default_factory=dict,
            description="The ingestor's settings for this database, as validated against its announced schema.",
        ),
    ]
    source: Annotated[
        str | None, Field(description="The deployed source pipeline that fills this database; null for manual upload.")
    ] = None
    source_configuration: Annotated[
        dict[str, Any],
        Field(default_factory=dict, description="The source's settings for this database, secret fields masked."),
    ]
    display_name: Annotated[str | None, Field(description="A user-friendly display name for the database.")] = None
    description: Annotated[str | None, Field(description="A brief description of the database's contents.")] = None
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
