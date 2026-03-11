from swiss_ai_hub.core.events.process.start.ProcessStartEvent import ProcessStartEvent
from swiss_ai_hub.core.events.process.work.agent.AgentWorkEvent import AgentWorkEvent

from playground.agents.AgentA.events.AgentAStopEvent import AgentAStopEvent


class AgentAWork(ProcessStartEvent, AgentWorkEvent[AgentAStopEvent]):
    pass
