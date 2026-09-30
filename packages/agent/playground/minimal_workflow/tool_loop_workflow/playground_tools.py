from typing import ClassVar

from playground.minimal_workflow.tool_loop_workflow.clock_tool import ClockTool
from swiss_ai_hub.agent.capabilities import Knowledge, ToolLoop


class PlaygroundTools:
    """The tools both playground agents offer: a capability tool and a function tool, side by side."""

    ALL: ClassVar[tuple] = ToolLoop.over(Knowledge, ClockTool.tool())
