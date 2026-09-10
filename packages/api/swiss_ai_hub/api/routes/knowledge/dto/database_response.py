from typing import Annotated, Any

from pydantic import BaseModel, Field


class DatabaseResponse(BaseModel):
    name: Annotated[str, Field(description="The database name (also the Milvus collection and Mongo store name).")]
    bucket_name: Annotated[str, Field(description="The S3 bucket / data lake container name.")]
    ingestor: Annotated[str, Field(description="The deployed ingestion pipeline that owns this database.")]
    configuration: Annotated[
        dict[str, Any],
        Field(description="The ingestor's settings for this database, as validated against its announced schema."),
    ] = {}
    source: Annotated[
        str | None, Field(description="The deployed source pipeline that fills this database; null for manual upload.")
    ] = None
    source_configuration: Annotated[
        dict[str, Any],
        Field(description="The source's settings for this database, secret fields masked."),
    ] = {}
    display_name: Annotated[str | None, Field(description="A user-friendly display name for the database.")] = None
    description: Annotated[str | None, Field(description="A brief description of the database's contents.")] = None
