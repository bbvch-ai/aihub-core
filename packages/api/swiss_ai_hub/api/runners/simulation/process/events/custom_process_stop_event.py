from swiss_ai_hub.core.events.process import ProcessStopEvent


class CustomProcessStopEvent(ProcessStopEvent):
    payload: str
