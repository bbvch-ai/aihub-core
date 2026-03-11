from swiss_ai_hub.core.events.agent.control.start.StartEvent import StartEvent


class AgentCStartEvent(StartEvent):
    payload: str
