from swiss_ai_hub.core.nats.events import ControlEvent


class FanOutA(ControlEvent):
    payload: str
