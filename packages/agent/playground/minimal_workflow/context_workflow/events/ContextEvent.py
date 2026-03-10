from swiss_ai_hub.core.nats.events.control.ControlEvent import ControlEvent


class ContextEvent(ControlEvent):
    thread_count: int
    run_count: int
