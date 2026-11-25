from typing import Annotated

from llama_index.core.vector_stores.types import FilterCondition, FilterOperator, MetadataFilter, MetadataFilters
from pydantic import BaseModel, Field, field_validator


class MetadataFilterPair(BaseModel):
    """A metadata key/value filter for RAG retrieval: the stored value equals it, or a stored list contains it.

    A list of texts is a choice: the stored value is one of them, or a stored list holds one of them.
    """

    key: Annotated[str, Field(description="The metadata key to filter on.")]
    value: Annotated[
        str | int | float | bool | list[str],
        Field(
            description="The value the metadata key must equal, or, where the key holds a list, contain. A list of "
            "texts matches any one of them."
        ),
    ]

    @field_validator("value")
    @classmethod
    def a_choice_is_never_empty(cls, value: str | int | float | bool | list[str]) -> str | int | float | bool | list[str]:
        """An empty choice would read as 'no filter' to some stores and as 'nothing' to others; the caller drops the
        retrieval instead."""
        if isinstance(value, list) and not value:
            raise ValueError("a list value needs at least one entry")
        return value

    def to_llama_index(self) -> MetadataFilter | MetadataFilters:
        """Text matches either shape, because Milvus never finds a string in a list by equality and the publisher
        cannot know which shape a document stored. Lists hold text only, so a number needs equality alone. A flag is
        compared as the text true/false: llama-index filters reject booleans, and ingestion stores flags as that text.
        """
        if isinstance(self.value, list):
            return MetadataFilters(
                filters=[
                    MetadataFilter(key=self.key, value=self.value, operator=FilterOperator.IN),
                    MetadataFilter(key=self.key, value=self.value, operator=FilterOperator.ANY),
                ],
                condition=FilterCondition.OR,
            )
        value = ("true" if self.value else "false") if isinstance(self.value, bool) else self.value
        equals = MetadataFilter(key=self.key, value=value)
        if not isinstance(value, str):
            return equals

        contains = MetadataFilter(key=self.key, value=value, operator=FilterOperator.CONTAINS)
        return MetadataFilters(filters=[equals, contains], condition=FilterCondition.OR)
