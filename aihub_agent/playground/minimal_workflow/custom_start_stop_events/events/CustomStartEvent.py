from pydantic import BaseModel

from aihub_lib.nats.events import StartEvent


class PydanticPayload(BaseModel):
    payload: str


class CustomStartEvent(StartEvent):
    payload: PydanticPayload
