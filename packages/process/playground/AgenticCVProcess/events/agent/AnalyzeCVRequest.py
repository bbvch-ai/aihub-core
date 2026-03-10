from typing import ClassVar

from swiss_ai_hub.core.nats.events.work.agent.AgentWorkEvent import AgentWorkEvent
from swiss_ai_hub.core.nats.events.work_request.agent.AgentWorkRequestEvent import AgentWorkRequestEvent

from playground.AgenticCVProcess.events.agent.AnalyzedCV import AnalyzedCV


class AnalyzeCVRequest(AgentWorkRequestEvent):
    submission: ClassVar[type[AgentWorkEvent]] = AnalyzedCV
