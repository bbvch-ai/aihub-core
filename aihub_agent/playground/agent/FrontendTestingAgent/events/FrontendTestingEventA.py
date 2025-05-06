from aihub_lib.nats.events import DisplayEvent, ControlEvent


class FrontendTestingEventA(DisplayEvent, ControlEvent):
    pass
