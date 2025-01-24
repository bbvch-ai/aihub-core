from aihub_lib.nats.events import ControlEvent


class FanOutA(ControlEvent):
    payload: str
