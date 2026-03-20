from swiss_ai_hub.core.events.agent import StopEvent


class AgentBStopEvent(StopEvent):
    payload: str
