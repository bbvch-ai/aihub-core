import json
from typing import Annotated, Self

from pydantic import BaseModel, Field

from aihub_lib.nats.events import WorkEvent


class ExternalProcessEvent(BaseModel):
    """Holds a work event that should be sent to a process given by its process class and process id."""

    process_class: Annotated[
        str,
        Field(description="Process class associated with this Work Event. "),
    ]
    process_id: Annotated[
        str,
        Field(description="Process ID associated with this Work Event. "),
    ]
    process_walkthrough_id: Annotated[
        str | None,
        Field(description="Walkthrough ID associated with this Work Event. "),
    ] = None
    event: Annotated[WorkEvent, Field(description="The user-originated event.")]

    @classmethod
    def deserialize_event(cls, data: bytes | str | dict) -> Self:
        """Deserialize incoming raw data (JSON string, bytes, or dict) into a ExternalProcessEvent."""
        if isinstance(data, dict):
            json_data = data
        elif isinstance(data, str):
            json_data = json.loads(data)
        elif isinstance(data, bytes):
            json_data = json.loads(data.decode())
        else:
            raise ValueError(f"Cannot deserialize data of type {type(data)}")

        event_json_data = json_data.get("event")
        event = WorkEvent.deserialize_event(event_json_data)

        return cls(process_class=json_data.get("process_class"), process_id=json_data.get("process_id"), event=event)
