from typing import Annotated

from llama_index.core.vector_stores.types import FilterCondition, FilterOperator, MetadataFilter, MetadataFilters
from pydantic import BaseModel, Field


class MetadataFilterPair(BaseModel):
    """A metadata key/value filter for RAG retrieval: the stored value equals it, or a stored list contains it."""

    key: Annotated[str, Field(description="The metadata key to filter on.")]
    value: Annotated[
        str | int | float | bool,
        Field(description="The value the metadata key must equal, or, where the key holds a list, contain."),
    ]

    def to_llama_index(self) -> MetadataFilter | MetadataFilters:
        """Text matches either shape, because Milvus never finds a string in a list by equality and the publisher
        cannot know which shape a document stored. Lists hold text only, so a number needs equality alone. A flag is
        compared as the text true/false: llama-index filters reject booleans, and ingestion stores flags as that text.
        """
        value = ("true" if self.value else "false") if isinstance(self.value, bool) else self.value
        equals = MetadataFilter(key=self.key, value=value)
        if not isinstance(value, str):
            return equals

        contains = MetadataFilter(key=self.key, value=value, operator=FilterOperator.CONTAINS)
        return MetadataFilters(filters=[equals, contains], condition=FilterCondition.OR)
