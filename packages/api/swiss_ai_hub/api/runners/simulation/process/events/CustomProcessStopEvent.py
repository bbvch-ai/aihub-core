from swiss_ai_hub.core.nats.events.process.stop.ProcessStopEvent import ProcessStopEvent


class CustomProcessStopEvent(ProcessStopEvent):
    payload: str
