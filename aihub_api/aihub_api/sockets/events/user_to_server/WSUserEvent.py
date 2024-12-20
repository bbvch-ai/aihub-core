import json

from pydantic import BaseModel, Field

from aihub_lib.nats.events.human_in_the_loop import HumanInTheLoopResponseEvent
from aihub_lib.nats.events.user.UserMessageEvent import UserMessageEvent


class WSUserEvent(BaseModel):
    """
    Represents an event received from a user over a WebSocket connection. It includes:
    - The `thread_id` and `display_id` indicating where this event should be routed.
    - A `UserMessageEvent` or `HumanInTheLoopResponseEvent` that the user sent.

    ### Why WSUserEvent?
    Users interact with the system via the frontend UI. Their actions—like sending messages, responding
    to prompts, or initiating runs—arrive at the server as raw data. `WSUserEvent`:
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
    After `WSUserEvent.deserialize_event(...)`, you get a `WSUserEvent` with a `UserMessageEvent` as `event`.
    """

    thread_id: str = Field(..., description="ID of the thread this event is related to.")
    display_id: str = Field(..., description="Display session ID, grouping events in the UI.")
    event: UserMessageEvent | HumanInTheLoopResponseEvent = Field(..., description="The user-originated event.")

    @classmethod
    def deserialize_event(cls, data: bytes | str | dict) -> 'WSUserEvent':
        """
        Deserialize incoming raw data (JSON string, bytes, or dict) into a WSUserEvent.

        Steps:
        1. Parse the raw data into a dictionary.
        2. Extract the `event` part and determine its type from the `_type` field.
        3. Depending on the `_type`, construct a `HumanInTheLoopResponseEvent` or `UserMessageEvent`.
        4. Return a WSUserEvent instance with the parsed event and identifiers (thread_id, display_id).

        Raises `ValueError` if the event type is unknown.
        """
        if isinstance(data, dict):
            json_data = data
        elif isinstance(data, str):
            json_data = json.loads(data)
        elif isinstance(data, bytes):
            json_data = json.loads(data.decode())
        else:
            raise ValueError(f"Cannot deserialize data of type {type(data)}")

        event_json_data = json_data.get("event")
        if event_json_data is None:
            raise ValueError("Event field is missing in the input")

        _type = event_json_data.get("_type")
        if _type is None:
            raise ValueError("No '_type' field in event")

        # Remove 'event' from the main dictionary before constructing WSUserEvent
        del json_data["event"]
        event_raw_data = json.dumps(event_json_data)

        if _type == "HumanInTheLoopResponseEvent":
            event_class = HumanInTheLoopResponseEvent.deserialize_event(event_json_data)
        elif _type == "UserMessageEvent":
            event_class = UserMessageEvent.deserialize_event(event_raw_data.encode())
        else:
            raise ValueError(f"Unknown event type: {_type}")

        return cls(event=event_class, **json_data)
