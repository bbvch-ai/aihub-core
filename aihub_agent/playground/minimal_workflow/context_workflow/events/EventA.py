from aihub_lib.nats.events import ControlEvent


class EventA(ControlEvent):
    thread_count: int
    run_count: int
