from aihub_lib.nats.events import ControlEvent


class ConfiguredEventA(ControlEvent):
    payload: str
