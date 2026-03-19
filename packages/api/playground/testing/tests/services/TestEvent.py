from typing import Annotated

from pydantic import BaseModel, Field
from swiss_ai_hub.core.events import BaseEvent


class Level3Model(BaseModel):
    deep_value: Annotated[str, Field(description="A deeply nested field")]
    deep_number: Annotated[int, Field(description="A deeply nested number")] = 999


class Level2Model(BaseModel):
    level3: Annotated[Level3Model, Field(description="Level 3 nested model")]
    level2_data: Annotated[str, Field(description="Level 2 data")]


class NestedTestModel(BaseModel):
    nested_field: Annotated[str, Field(description="A nested field")]
    nested_optional: Annotated[int | None, Field(description="An optional nested field")] = None
    level2: Annotated[Level2Model | None, Field(description="Deep nesting test")] = None


class TestEvent(BaseEvent):
    test_field: Annotated[str, Field(description="A test field for JSON schema conversion")]
    test_field_with_default: Annotated[
        int, Field(description="A test field with default value for JSON schema conversion")
    ] = 42
    nested_model: Annotated[NestedTestModel, Field(description="A nested Pydantic model")]
    optional_nested: Annotated[NestedTestModel | None, Field(description="An optional nested model")] = None
    union_field: Annotated[str | int, Field(description="A union type field")]
    complex_union: Annotated[str | NestedTestModel, Field(description="Union with nested model")]
    list_of_nested: Annotated[list[NestedTestModel], Field(description="List of nested models")]
    optional_union: Annotated[str | int | None, Field(description="Optional union type")] = None
