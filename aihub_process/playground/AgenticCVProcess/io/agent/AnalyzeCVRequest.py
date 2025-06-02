from typing import ClassVar, Type

from aihub_process.process.io.agent.AgentWork import AgentWork
from aihub_process.process.io.agent.AgentWorkRequest import AgentWorkRequest
from playground.AgenticCVProcess.io.agent.AnalyzedCV import AnalyzedCV


class AnalyzeCVRequest(AgentWorkRequest):
    submission: ClassVar[Type[AgentWork]] = AnalyzedCV