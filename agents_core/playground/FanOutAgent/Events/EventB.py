from lib_core.nats.events import ControlEvent


class EventB(ControlEvent):
    payload: str
