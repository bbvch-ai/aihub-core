from aihub_lib.nats.events import ControlEvent, DisplayEvent


class FrontendTestingEventA(DisplayEvent, ControlEvent):
    pass
