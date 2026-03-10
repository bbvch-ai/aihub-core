import json
from typing import Annotated, Self

from bson import ObjectId
from pydantic import BaseModel, Field

from swiss_ai_hub.core.nats.events import ControlEvent


class ExternalAgentEvent(BaseModel):
    """
    Represents an event received from an external system like websockets or bot framework. It includes:
    - The `thread_id` and `display_id` indicating where this event should be routed.
    - A `UserMessageEvent` or `HumanInTheLoopResponseEvent` that the user sent.

    ### Why ExternalAgentEvent?
    Users interact with the system via some service. Their actions - like sending messages, responding
    to prompts, or initiating runs - arrive at the server as raw data. `ExternalAgentEvent`:
    - Parses and validates the incoming JSON or binary data.
    - Identifies the event type and instantiates the appropriate event class.
    - Provides a consistent structure for the server to understand user intentions.

    ### Deserialization
    `deserialize_event` inspects the `_type` field of the `event` payload to determine if it's
    a `HumanInTheLoopResponseEvent` or a `UserMessageEvent`. It then uses the corresponding deserialization
    logic from those event classes.

    ### Example
    Suppose the frontend sends:
    ```json
    {
      "thread_id": "thread123",
      "display_id": "displayA",
      "event": {
        "_event_name": "UserMessageEvent",
        "content": "Hello world!"
      }
    }
    ```
    After `ExternalAgentEvent.deserialize_event(...)`, you get a `ExternalAgentEvent`
    with a `UserMessageEvent` as `event`.
    """

    thread_id: Annotated[str, Field(description="ID of the thread this event is related to.")]
    display_id: Annotated[str, Field(description="Display session ID, grouping events in the UI.")]
    event: Annotated[ControlEvent, Field(description="The user-originated event.")]

    @classmethod
    def deserialize_event(cls, data: bytes | str | dict) -> Self:
        """Deserialize incoming raw data (JSON string, bytes, or dict) into a ExternalAgentEvent."""
        if isinstance(data, dict):
            json_data = data
        elif isinstance(data, str):
            json_data = json.loads(data)
        elif isinstance(data, bytes):
            json_data = json.loads(data.decode())
        else:
            raise ValueError(f"Cannot deserialize data of type {type(data)}")

        event_json_data = json_data.get("event")
        event = ControlEvent.deserialize_event(event_json_data)

        return cls(
            thread_id=json_data.get("thread_id"),
            display_id=json_data.get("display_id", str(ObjectId())),
            event=event,
        )
