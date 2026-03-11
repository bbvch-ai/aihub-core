from swiss_ai_hub.core.events.agent.control.start.StartEvent import StartEvent


class CustomStartEvent(StartEvent):
    payload: str
