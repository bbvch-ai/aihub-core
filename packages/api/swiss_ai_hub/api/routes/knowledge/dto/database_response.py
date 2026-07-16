from typing import Annotated

from pydantic import BaseModel, Field


class DatabaseResponse(BaseModel):
    name: Annotated[str, Field(description="The database name (also the Milvus collection and Mongo store name).")]
    bucket_name: Annotated[str, Field(description="The S3 bucket / data lake container name.")]
    # Deliberately a plain str, not the IngestorType enum: a customer-specific deployment can register a
    # custom pipeline via IngestorRegistry and assign databases to it, so this value is not limited to the
    # platform enum. Typing it as IngestorType would bake a closed set into the OpenAPI schema/SDK and make
    # custom ingestors unrepresentable on the wire.
    ingestor: Annotated[str, Field(description="The deployed ingestion pipeline that owns this database.")]
    display_name: Annotated[str | None, Field(description="A user-friendly display name for the database.")] = None
    description: Annotated[str | None, Field(description="A brief description of the database's contents.")] = None
