from aihub_lib.nats.events import ControlEvent


class EventConfiguredA(ControlEvent):
    payload: str
