from swiss_ai_hub.core.events.process import AgentWorkEvent

from playground.agents.agent_c.events.agent_c_stop_event import AgentCStopEvent


class AgentCWork(AgentWorkEvent[AgentCStopEvent]):
    pass
