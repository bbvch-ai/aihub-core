from aihub_lib.nats.events.work.human.HumanWorkEvent import HumanWorkEvent


class AcceptCV(HumanWorkEvent):
    reason: str
