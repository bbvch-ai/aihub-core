from typing import ClassVar, Type

from aihub_lib.nats.events.work.human.HumanWorkEvent import HumanWorkEvent
from aihub_lib.nats.events.work_request.human.HumanWorkRequestEvent import HumanWorkRequestEvent
from playground.AgenticCVProcess.events.human.AcceptCV import AcceptCV
from playground.AgenticCVProcess.events.human.RejectCV import RejectCV


class AcceptRejectRequest(HumanWorkRequestEvent):
    accept: ClassVar[Type[HumanWorkEvent]] = AcceptCV
    reject: ClassVar[Type[HumanWorkEvent]] = RejectCV
