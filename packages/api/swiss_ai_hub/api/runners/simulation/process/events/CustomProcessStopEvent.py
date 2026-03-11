from swiss_ai_hub.core.events.process.stop.ProcessStopEvent import ProcessStopEvent


class CustomProcessStopEvent(ProcessStopEvent):
    payload: str
