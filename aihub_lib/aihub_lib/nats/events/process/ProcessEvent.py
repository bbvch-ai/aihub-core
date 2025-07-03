from aihub_lib.nats.events import BaseEvent


class ProcessEvent(BaseEvent):
    """
    All events that influence the control flow of a process must inherit from this class.
    """

    pass
