from aihub_lib.nats.events import StartEvent


class CustomStartEvent(StartEvent):
    payload: str
