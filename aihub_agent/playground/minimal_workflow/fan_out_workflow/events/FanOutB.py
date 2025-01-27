from aihub_lib.nats.events import ControlEvent


class FanOutB(ControlEvent):
    payload: str
