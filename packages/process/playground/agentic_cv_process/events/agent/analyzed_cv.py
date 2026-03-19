from swiss_ai_hub.core.events.agent import LLMStopEvent
from swiss_ai_hub.core.events.process import AgentWorkEvent


class AnalyzedCV(AgentWorkEvent[LLMStopEvent]):
    pass
