import json

from pydantic import BaseModel

from lib_core.nats.events.human_in_the_loop import HumanInTheLoopResponseEvent
from lib_core.nats.events.user.UserMessageEvent import UserMessageEvent


class WSUserEvent(BaseModel):
    thread_id: str
    display_id: str
    event: UserMessageEvent | HumanInTheLoopResponseEvent

    @classmethod
    def deserialize_event(cls, data: bytes | str | dict) -> 'WSUserEvent':
        if isinstance(data, dict):
            json_data = data
        elif isinstance(data, str):
            json_data = json.loads(data)
        elif isinstance(data, bytes):
            json_data = json.loads(data.decode())
        else:
            raise ValueError(f"Cannot deserialize data of type {type(data)}")
        event_json_data = json_data.get("event")

        _type = event_json_data.get("_type")
        del json_data["event"]
        event_raw_data = json.dumps(event_json_data)

        if _type == "HumanInTheLoopResponseEvent":
            event_class = HumanInTheLoopResponseEvent.deserialize_event(event_json_data)
        elif _type == "UserMessageEvent":
            event_class = UserMessageEvent.deserialize_event(event_raw_data.encode())
        else:
            raise ValueError(f"Unknown event type: {_type}")

        return cls(
            event=event_class,
            **json_data
        )
