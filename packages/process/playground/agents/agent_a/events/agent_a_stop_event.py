from swiss_ai_hub.core.events.agent import StopEvent


class AgentAStopEvent(StopEvent):
    payload: str
