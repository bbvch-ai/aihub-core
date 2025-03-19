from pydantic import BaseModel

from aihub_lib.nats.events import StartEvent


class PydanticPayload(BaseModel):
    payload: str


class MyCustomStartEvent(StartEvent):
    payload: PydanticPayload
