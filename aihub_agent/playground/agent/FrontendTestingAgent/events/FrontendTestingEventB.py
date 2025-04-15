from aihub_lib.nats.events import DisplayEvent, ControlEvent


class FrontendTestingEventB(DisplayEvent, ControlEvent):
    pass