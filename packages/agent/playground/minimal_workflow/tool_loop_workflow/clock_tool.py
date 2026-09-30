from datetime import datetime
from typing import Annotated
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field

from swiss_ai_hub.agent.capabilities import FunctionTool, ToolContext


class CurrentTimeArguments(BaseModel):
    timezone: Annotated[str, Field(description="IANA time zone, e.g. Europe/Zurich.")] = "Europe/Zurich"


class ClockTool:
    """A function tool: tells the model the current time, which it cannot know on its own."""

    @staticmethod
    async def run(arguments: CurrentTimeArguments, context: ToolContext) -> str:
        return datetime.now(ZoneInfo(arguments.timezone)).isoformat(timespec="minutes")

    @classmethod
    def tool(cls) -> FunctionTool:
        return FunctionTool(
            name="current_time",
            description="The current date and time in a time zone. Use it whenever the answer depends on today.",
            arguments=CurrentTimeArguments,
            run=cls.run,
        )
