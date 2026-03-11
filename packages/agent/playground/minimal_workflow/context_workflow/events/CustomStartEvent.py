from swiss_ai_hub.core.events.agent import StartEvent


class CustomStartEvent(StartEvent):
    payload: str
