from pydantic import BaseModel
from swiss_ai_hub.core.nats.events import StartEvent


class PydanticPayload(BaseModel):
    payload: str


class MyCustomStartEvent(StartEvent):
    payload: PydanticPayload
