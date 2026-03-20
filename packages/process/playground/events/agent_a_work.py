from swiss_ai_hub.core.events.process import AgentWorkEvent, ProcessStartEvent

from playground.agents.agent_a.events.agent_a_stop_event import AgentAStopEvent


class AgentAWork(ProcessStartEvent, AgentWorkEvent[AgentAStopEvent]):
    pass
