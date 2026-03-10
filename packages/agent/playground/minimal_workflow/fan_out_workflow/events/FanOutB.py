from swiss_ai_hub.core.nats.events.control.ControlEvent import ControlEvent


class FanOutB(ControlEvent):
    payload: str
