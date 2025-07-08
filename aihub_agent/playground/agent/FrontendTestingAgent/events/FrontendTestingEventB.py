from aihub_lib.nats.events import ControlEvent, DisplayEvent


class FrontendTestingEventB(DisplayEvent, ControlEvent):
    pass
