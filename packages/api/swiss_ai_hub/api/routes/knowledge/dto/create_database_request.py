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
    # Deliberately a plain str, not the IngestorType enum, so a database can be assigned to a custom pipeline
    # registered via IngestorRegistry. The value is validated against the registry in create_database.
    ingestor: Annotated[
        str, Field(description="The deployed ingestion pipeline that processes this database's documents.")
    ] = IngestorType.RAG.value
