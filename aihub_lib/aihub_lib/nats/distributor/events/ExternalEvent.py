import json

from pydantic import BaseModel, Field

from aihub_lib.nats.events import StartEvent, ControlEvent, BaseEvent
from aihub_lib.nats.events.human_in_the_loop import HumanInTheLoopResponseEvent
from aihub_lib.nats.events.user.UserMessageEvent import UserMessageEvent


class ExternalEvent(BaseModel):
    """
    Represents an event received from an external system like websockets or bot framework. It includes:
    - The `thread_id` and `display_id` indicating where this event should be routed.
    - A `UserMessageEvent` or `HumanInTheLoopResponseEvent` that the user sent.

    ### Why ExternalEvent?
    Users interact with the system via some service. Their actions—like sending messages, responding
    to prompts, or initiating runs—arrive at the server as raw data. `ExternalEvent`:
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
        "_type": "UserMessageEvent",
        "content": "Hello world!"
      }
    }
    ```
    After `ExternalEvent.deserialize_event(...)`, you get a `ExternalEvent` with a `UserMessageEvent` as `event`.
    """

    thread_id: str = Field(..., description="ID of the thread this event is related to.")
    display_id: str = Field(..., description="Display session ID, grouping events in the UI.")
    event: ControlEvent = Field(
        ..., description="The user-originated event."
    )

    @classmethod
    def deserialize_event(cls, data: bytes | str | dict) -> "ExternalEvent":
        """Deserialize incoming raw data (JSON string, bytes, or dict) into a ExternalEvent."""
        if isinstance(data, dict):
            json_data = data
        elif isinstance(data, str):
            json_data = json.loads(data)
        elif isinstance(data, bytes):
            json_data = json.loads(data.decode())
        else:
            raise ValueError(f"Cannot deserialize data of type {type(data)}")


        thread_id = json_data.get("thread_id")
        display_id = json_data.get("display_id")

        event_json_data = json_data.get("event")
        event = BaseEvent.deserialize_event(event_json_data)

        return cls(
            thread_id=thread_id,
            display_id=display_id,
            event=event,
        )
