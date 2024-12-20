from aihub_lib.nats.events import ControlEvent


class EventA(ControlEvent):
    payload: str
