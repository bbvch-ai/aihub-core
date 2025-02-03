from aihub_lib.nats.events import ControlEvent


class RightAgentEvent(ControlEvent):
    success: bool
    reasoning: str
