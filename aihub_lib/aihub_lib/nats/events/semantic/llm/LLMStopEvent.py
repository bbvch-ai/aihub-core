from .LLMEvent import LLMEvent
from ...control import StopEvent


class LLMStopEvent(LLMEvent, StopEvent):
    pass
