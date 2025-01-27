from aihub_lib.nats.events import ControlEvent


class ContextEvent(ControlEvent):
    thread_count: int
    run_count: int