from typing import ClassVar

from aihub_lib.nats.events.work.agent.AgentWorkEvent import AgentWorkEvent
from aihub_lib.nats.events.work_request.agent.AgentWorkRequestEvent import AgentWorkRequestEvent

from playground.AgenticCVProcess.events.agent.AnalyzedCV import AnalyzedCV


class AnalyzeCVRequest(AgentWorkRequestEvent):
    submission: ClassVar[type[AgentWorkEvent]] = AnalyzedCV
