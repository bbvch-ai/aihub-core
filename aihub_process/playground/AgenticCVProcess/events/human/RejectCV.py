from aihub_lib.nats.events.work.human.HumanWorkEvent import HumanWorkEvent


class RejectCV(HumanWorkEvent):
    reason: str
