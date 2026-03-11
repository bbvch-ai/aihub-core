from swiss_ai_hub.core.events.process import AgentWorkEvent, ProcessStartEvent

from playground.agents.AgentA.events.AgentAStopEvent import AgentAStopEvent


class AgentAWork(ProcessStartEvent, AgentWorkEvent[AgentAStopEvent]):
    pass
