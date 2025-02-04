from aihub_lib.nats.events import ControlEvent


class FewShotAcceptEvent(ControlEvent):
    success: bool
    reasoning: str
