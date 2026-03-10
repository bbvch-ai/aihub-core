from swiss_ai_hub.core.nats.events import ProcessStopEvent


class CustomProcessStopEvent(ProcessStopEvent):
    payload: str
