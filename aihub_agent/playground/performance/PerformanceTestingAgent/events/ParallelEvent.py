from aihub_lib.nats.events import ControlEvent


class ParallelEvent(ControlEvent):
    index: int
    payload: str
