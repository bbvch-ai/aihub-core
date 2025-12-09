from enum import Enum
from typing import Annotated

from pydantic import BaseModel, Field


class RetrieverType(str, Enum):
    """Type of retriever."""

    KNOWLEDGE = "knowledge"
    INSIGHT = "insight"


class BaseRetrieverConfig(BaseModel):
    """Base configuration for all retrievers."""

    retriever_type: Annotated[RetrieverType, Field(description="Type of retriever")]
    enabled: Annotated[bool, Field(description="Whether this retriever is enabled")] = True
