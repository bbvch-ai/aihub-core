from swiss_ai_hub.core.events.agent import StopEvent


class AgentCStopEvent(StopEvent):
    payload: str
