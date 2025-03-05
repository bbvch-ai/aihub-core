from aihub_lib.nats.events import ControlEvent


class ContextInsufficientEvent(ControlEvent):
    reasoning: str
