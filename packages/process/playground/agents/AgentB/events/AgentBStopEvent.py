from swiss_ai_hub.core.events.agent.control.stop.StopEvent import StopEvent


class AgentBStopEvent(StopEvent):
    payload: str
