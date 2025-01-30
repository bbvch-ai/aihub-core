from aihub_lib.nats.events import ControlEvent


class SimpleEventA(ControlEvent):
    payload: str
