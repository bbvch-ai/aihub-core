from aihub_lib.nats.events import ControlEvent


class ParallelEvent(ControlEvent):
    payload: str
