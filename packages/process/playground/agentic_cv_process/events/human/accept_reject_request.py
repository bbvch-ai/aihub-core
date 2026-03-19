from typing import ClassVar

from swiss_ai_hub.core.events.process import HumanWorkRequestEvent

from playground.agentic_cv_process.events.human.accept_cv import AcceptCV
from playground.agentic_cv_process.events.human.reject_cv import RejectCV


class AcceptRejectRequest(HumanWorkRequestEvent):
    accept: ClassVar[type[AcceptCV]] = AcceptCV
    reject: ClassVar[type[RejectCV]] = RejectCV
