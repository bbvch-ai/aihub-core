from swiss_ai_hub.core.nats.events import ControlEvent


class ParallelEvent(ControlEvent):
    payload: str
