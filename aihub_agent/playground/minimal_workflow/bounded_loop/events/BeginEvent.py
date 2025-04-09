from aihub_lib.nats.events import ControlEvent


class BeginEvent(ControlEvent):
    count: int
