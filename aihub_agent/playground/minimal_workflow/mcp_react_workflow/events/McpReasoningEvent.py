from aihub_lib.nats.events import ControlEvent
from aihub_lib.nats.events.semantic.llm.Message import Message


class McpReasoningEvent(ControlEvent):
    """Triggers the next LLM reasoning iteration, carrying the full conversation."""

    messages: list[Message]
