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
    ingestor: Annotated[
        IngestorType, Field(description="The deployed ingestion pipeline that processes this database's documents.")
    ] = IngestorType.RAG
