from aihub_lib.nats.events import ControlEvent


class FanOutEventB(ControlEvent):
    payload: str
