from aihub_lib.nats.events import ControlEvent


class EventConfiguredB(ControlEvent):
    payload: str
