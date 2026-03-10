from swiss_ai_hub.core.nats.events.BaseEvent import BaseEvent


class ControlEvent(BaseEvent):
    """
    Represents a system-level or workflow-level signal, often used to coordinate steps,
    indicate state changes, or trigger specific actions in the event-driven architecture.

    ### Why ControlEvent?
    While `BaseEvent` covers the general structure for any event, `ControlEvent` marks an event as
    particularly important for controlling the flow of a system. Hence, all events taken as inputs to
    workflow steps must be of type `ControlEvent`. Even though other type of events can be returned
    from workflow steps, only 'ControlEvent' influence the flow of the system.

    By subclassing `BaseEvent`, `ControlEvent` benefits from automatic type registration and
    serialization, ensuring that control signals are as easy to produce and consume as any other event.
    """

    pass
