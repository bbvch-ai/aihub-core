from swiss_ai_hub.core.events.agent import StartEvent


class AgentCStartEvent(StartEvent):
    payload: str
