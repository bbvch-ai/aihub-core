from swiss_ai_hub.core.events.process import AgentWorkEvent

from playground.agents.agent_b.events.agent_b_stop_event import AgentBStopEvent


class AgentBWork(AgentWorkEvent[AgentBStopEvent]):
    pass
