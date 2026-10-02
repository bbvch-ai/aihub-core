from datetime import datetime
from typing import Annotated
from zoneinfo import ZoneInfo

from llama_index.core.tools.tool_spec.base import BaseToolSpec
from swiss_ai_hub.core.i18n import LocaleString

from swiss_ai_hub.agent.capabilities import ToolContext, ToolOptions


class ClockTools(BaseToolSpec):
    """Function tools as a LlamaIndex tool spec: every listed method is a tool, its schema read from the signature."""

    spec_functions = ["current_time"]

    def __init__(self, context: ToolContext) -> None:
        self.context = context

    @ToolOptions.of(label=LocaleString(en="Clock", de="Uhr", fr="Horloge", it="Orologio"))
    async def current_time(
        self, timezone: Annotated[str, "IANA time zone, e.g. Europe/Zurich"] = "Europe/Zurich"
    ) -> str:
        """The current date and time in a time zone. Use it whenever the answer depends on today."""
        return datetime.now(ZoneInfo(timezone)).isoformat(timespec="minutes")
