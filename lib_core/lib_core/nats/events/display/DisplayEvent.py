from lib_core.nats.events.BaseEvent import BaseEvent


class DisplayEvent(BaseEvent):
    """
    Represents a user-facing event that can be shown to end-users, UIs, or monitoring dashboards.
    Display events are purely informational and never affect the control flow or execution order
    of workflows.

    ### Why DisplayEvent?
    While `ControlEvent` influences the system’s decision-making and progression, `DisplayEvent`
    focuses on communicating results, status updates, and other information intended for human
    consumption or passive observation. This separation ensures that even if a display event fails
    to reach a UI, it doesn’t alter the underlying workflow logic or state transitions.

    By subclassing `BaseEvent`, `DisplayEvent` remains fully compatible with the automatic
    registration, serialization, and deserialization mechanisms, making it simple to integrate
    into a user interface or logging pipeline.
    """
    pass
