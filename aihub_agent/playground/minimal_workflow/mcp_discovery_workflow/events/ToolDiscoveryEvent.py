from typing import Annotated

from aihub_lib.nats.events import ControlEvent
from pydantic import Field


class ToolDiscoveryEvent(ControlEvent):
    """Emitted after MCP tools have been discovered."""

    tool_names: Annotated[list[str], Field(description="Names of discovered MCP tools.")]
