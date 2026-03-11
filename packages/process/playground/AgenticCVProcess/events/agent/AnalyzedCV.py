from swiss_ai_hub.core.events.agent.semantic.llm.LLMStopEvent import LLMStopEvent
from swiss_ai_hub.core.events.process.work.agent.AgentWorkEvent import AgentWorkEvent


class AnalyzedCV(AgentWorkEvent[LLMStopEvent]):
    pass
