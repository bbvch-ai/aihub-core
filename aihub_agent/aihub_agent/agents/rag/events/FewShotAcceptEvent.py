from aihub_lib.nats.events import ControlEvent


class FewShotAcceptEvent(ControlEvent):
    reasoning: str
