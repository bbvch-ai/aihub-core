from aihub_lib.nats.events import ControlEvent


class ConfiguredEventB(ControlEvent):
    payload: str
