from swiss_ai_hub.core.nats.events.control.ControlEvent import ControlEvent


class FanOutA(ControlEvent):
    payload: str
