from swiss_ai_hub.core.events.agent import StartEvent


class AgentAStartEvent(StartEvent):
    payload: str
