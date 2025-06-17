from aihub_lib.nats.events import ProcessStopEvent


class CustomProcessStopEvent(ProcessStopEvent):
    payload: str
