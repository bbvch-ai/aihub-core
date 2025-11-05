from typing import Annotated

from pydantic import Field

from aihub_lib.nats.events import BaseEvent


class SourceUpdatedEvent(BaseEvent):
    filename: Annotated[str, Field(description="Original filename of the file", min_length=1, max_length=255)]
    content_type: Annotated[str, Field(description="MIME type of the file")]
    content_length: Annotated[int, Field(description="Size of the file in bytes", gt=0)]
    path: Annotated[str, Field(description="The object path for the uploaded file")]
