from typing import Any

from aihub_lib.nats.events import ControlEvent
from aihub_lib.nats.events.semantic.llm.Message import Message


class McpToolCallEvent(ControlEvent):
    """Emitted when the LLM requests tool calls — carries calls and conversation to the execution step."""

    tool_calls: list[dict[str, Any]]
    messages: list[Message]
