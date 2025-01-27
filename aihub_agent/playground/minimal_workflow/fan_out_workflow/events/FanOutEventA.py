from aihub_lib.nats.events import ControlEvent


class FanOutEventA(ControlEvent):
    payload: str
