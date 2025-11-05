from typing import Annotated

from pydantic import Field

from aihub_lib.nats.events import BaseEvent


class SourceUpdatedEvent(BaseEvent):
    path: Annotated[str, Field(description="The object path for the uploaded file")]
