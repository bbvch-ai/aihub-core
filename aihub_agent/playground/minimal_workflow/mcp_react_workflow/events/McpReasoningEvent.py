from typing import Any

from aihub_lib.nats.events import ControlEvent


class McpReasoningEvent(ControlEvent):
    """Triggers the next LLM reasoning iteration, carrying the full conversation."""

    messages: list[dict[str, Any]]
