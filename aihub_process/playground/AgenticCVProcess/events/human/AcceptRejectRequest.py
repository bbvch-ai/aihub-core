from typing import ClassVar

from aihub_lib.nats.events.work_request.human.HumanWorkRequestEvent import HumanWorkRequestEvent
from playground.AgenticCVProcess.events.human.AcceptCV import AcceptCV
from playground.AgenticCVProcess.events.human.RejectCV import RejectCV


class AcceptRejectRequest(HumanWorkRequestEvent):
    accept: ClassVar[type[AcceptCV]] = AcceptCV
    reject: ClassVar[type[RejectCV]] = RejectCV

