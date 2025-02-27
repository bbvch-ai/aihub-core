from aihub_lib.nats.events import ControlEvent


class FewShotRejectEvent(ControlEvent):
    reasoning: str
