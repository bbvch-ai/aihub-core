from typing import Annotated

from pydantic import BaseModel, Field


class DatabaseResponse(BaseModel):
    name: Annotated[str, Field(description="The database name (also the Milvus collection and Mongo store name).")]
    bucket_name: Annotated[str, Field(description="The S3 bucket / data lake container name.")]
    ingestor: Annotated[str, Field(description="The deployed ingestion pipeline that owns this database.")]
    display_name: Annotated[str | None, Field(description="A user-friendly display name for the database.")] = None
    description: Annotated[str | None, Field(description="A brief description of the database's contents.")] = None
