from swiss_ai_hub.core.nats.events import ControlEvent


class FanOutB(ControlEvent):
    payload: str
