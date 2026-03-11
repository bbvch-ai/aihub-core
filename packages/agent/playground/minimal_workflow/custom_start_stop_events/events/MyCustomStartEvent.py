from pydantic import BaseModel
from swiss_ai_hub.core.events.agent.control.start.StartEvent import StartEvent


class PydanticPayload(BaseModel):
    payload: str


class MyCustomStartEvent(StartEvent):
    payload: PydanticPayload
