from lib_core.nats.events import StartEvent


class CustomStartEvent(StartEvent):
    payload: str