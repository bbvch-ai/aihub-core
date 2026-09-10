from typing import Annotated

from pydantic import BaseModel, Field


class BatchDeleteDocumentsRequest(BaseModel):
    """Request payload for deleting multiple documents from a knowledge namespace."""

    document_ids: Annotated[
        list[str], Field(description="IDs of the documents to delete", min_length=1, max_length=100)
    ]
