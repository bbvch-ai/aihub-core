from swiss_ai_hub.core.events.agent import LLMEvent


class McpReasoningEvent(LLMEvent):
    """Triggers the next LLM reasoning iteration, carrying the full conversation."""
