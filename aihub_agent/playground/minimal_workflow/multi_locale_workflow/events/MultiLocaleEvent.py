from aihub_lib.nats.events import ControlEvent


class MultiLocaleEvent(ControlEvent):
    payload: str
