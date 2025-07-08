from aihub_lib.nats.events import StartEvent
from pydantic import BaseModel


class PydanticPayload(BaseModel):
    payload: str


class MyCustomStartEvent(StartEvent):
    payload: PydanticPayload
