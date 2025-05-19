from typing import Annotated, List

from pydantic import BaseModel, Field


class Namespace(BaseModel):
    database: Annotated[str, Field(..., description="Name of database that the namespace belongs to")]
    name: Annotated[str, Field(..., description="Name of namespace")]
    number_of_documents: Annotated[int, Field(..., description="Number of documents in namespace")]
    last_updated_at: Annotated[
        int, Field(..., description="Latest timestamp when any document in the namespace was updated")
    ]
    last_inserted_at: Annotated[
        int, Field(..., description="Latest timestamp when any document in the namespace was inserted")
    ]
    created_at: Annotated[
        int, Field(..., description="Oldest timestamp when any document in the namespace was created")
    ]
    document_types: Annotated[List[str], Field(..., description="Set of all document types in the namespace")]
