from ...control import StopEvent
from .LLMEvent import LLMEvent


class LLMStopEvent(LLMEvent, StopEvent):
    pass
