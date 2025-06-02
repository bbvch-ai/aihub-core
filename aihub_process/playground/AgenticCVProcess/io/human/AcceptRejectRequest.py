from typing import ClassVar, Type

from aihub_process.process.io.human.HumanWork import HumanWork
from aihub_process.process.io.human.HumanWorkRequest import HumanWorkRequest
from playground.AgenticCVProcess.io.human.AcceptCV import AcceptCV
from playground.AgenticCVProcess.io.human.RejectCV import RejectCV


class AcceptRejectRequest(HumanWorkRequest):
    accept: ClassVar[Type[HumanWork]] = AcceptCV
    reject: ClassVar[Type[HumanWork]] = RejectCV
