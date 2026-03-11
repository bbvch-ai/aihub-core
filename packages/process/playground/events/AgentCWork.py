from swiss_ai_hub.core.events.process import AgentWorkEvent

from playground.agents.AgentC.events.AgentCStopEvent import AgentCStopEvent


class AgentCWork(AgentWorkEvent[AgentCStopEvent]):
    pass
