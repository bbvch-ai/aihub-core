from typing import ClassVar

from aihub_lib.nats.events.work.human.HumanWorkEvent import HumanWorkEvent
from aihub_lib.nats.events.work_request.human.HumanWorkRequestEvent import HumanWorkRequestEvent

from playground.AgenticCVProcess.events.human.AcceptCV import AcceptCV
from playground.AgenticCVProcess.events.human.RejectCV import RejectCV


class AcceptRejectRequest(HumanWorkRequestEvent):
    accept: ClassVar[type[HumanWorkEvent]] = AcceptCV
    reject: ClassVar[type[HumanWorkEvent]] = RejectCV
