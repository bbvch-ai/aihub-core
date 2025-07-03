from typing import Annotated, Optional

from pydantic import BaseModel, Field

from aihub_lib.nats.events import BaseEvent


class NestedTestModel(BaseModel):
    nested_field: Annotated[str, Field(description="A nested field")]
    nested_optional: Annotated[Optional[int], Field(description="An optional nested field")] = None


class TestEvent(BaseEvent):
    test_field: Annotated[str, Field(description="A test field for JSON schema conversion")]
    test_field_with_default: Annotated[
        int, Field(description="A test field with default value for JSON schema conversion")
    ] = 42
    nested_model: Annotated[NestedTestModel, Field(description="A nested Pydantic model")]
    optional_nested: Annotated[Optional[NestedTestModel], Field(description="An optional nested model")] = None
