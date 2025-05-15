from typing import Annotated

from pydantic import BaseModel, Field


class Namespace(BaseModel):
    name: Annotated[str, Field(..., description="Name of namespace")]
    number_of_documents: Annotated[int, Field(..., description="Number of documents in namespace")]