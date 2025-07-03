from typing import Annotated

from pydantic import Field

from aihub_lib.nats.events import BaseEvent


class TestEvent(BaseEvent):
    test_field: Annotated[str, Field(description="A test field for JSON schema conversion")]
    test_field_with_default: Annotated[
        int, Field(description="A test field with default value for JSON schema conversion")
    ] = 42
