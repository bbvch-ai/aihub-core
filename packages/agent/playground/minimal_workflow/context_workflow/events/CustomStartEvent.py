from swiss_ai_hub.core.nats.events import StartEvent


class CustomStartEvent(StartEvent):
    payload: str
