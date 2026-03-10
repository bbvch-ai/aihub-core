from swiss_ai_hub.core.nats.events.control.start.StartEvent import StartEvent


class CustomStartEvent(StartEvent):
    payload: str
