from aihub_lib.nats.events.semantic.llm.LLMEvent import LLMEvent


class McpReasoningEvent(LLMEvent):
    """Triggers the next LLM reasoning iteration, carrying the full conversation."""
