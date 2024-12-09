from lib_core.nats.events import LLMEvent, StopEvent


class LLMStopEvent(LLMEvent, StopEvent):
    pass