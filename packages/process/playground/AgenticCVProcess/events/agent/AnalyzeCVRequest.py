from typing import ClassVar

from swiss_ai_hub.core.events.process import AgentWorkEvent
from swiss_ai_hub.core.events.process import AgentWorkRequestEvent

from playground.AgenticCVProcess.events.agent.AnalyzedCV import AnalyzedCV


class AnalyzeCVRequest(AgentWorkRequestEvent):
    submission: ClassVar[type[AgentWorkEvent]] = AnalyzedCV
