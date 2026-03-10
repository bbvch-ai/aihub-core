from swiss_ai_hub.core.nats.events import ControlEvent


class BeginEvent(ControlEvent):
    count: int
