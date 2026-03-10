from swiss_ai_hub.core.nats.events import LLMStopEvent
from swiss_ai_hub.core.nats.events.work.agent.AgentWorkEvent import AgentWorkEvent


class AnalyzedCV(AgentWorkEvent[LLMStopEvent]):
    pass
