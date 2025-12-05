"""Base configuration for retriever implementations."""

from typing import Annotated, Literal

from pydantic import BaseModel, Field

RetrieverType = Literal["knowledge", "insight"]


class BaseRetrieverConfig(BaseModel):
    """
    Base configuration for all retriever types.

    This provides common fields that all retrievers share:
    - retriever_type: Discriminator for factory instantiation
    - name: Human-readable identifier
    - enabled: Toggle for runtime activation
    """

    retriever_type: Annotated[RetrieverType, Field(description="The type of retriever")]
    name: Annotated[str, Field(description="Human-readable name for this retriever")]
    enabled: Annotated[bool, Field(description="Whether this retriever is active")] = True
