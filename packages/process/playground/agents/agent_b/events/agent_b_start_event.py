from swiss_ai_hub.core.events.agent import StartEvent


class AgentBStartEvent(StartEvent):
    payload: str
