from typing import Annotated, ClassVar

from pydantic import Field

from swiss_ai_hub.core.events.agent.display.display_event import DisplayEvent
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class ToolLoopCondensedEvent(DisplayEvent):
    """The tool loop condensed its conversation to fit the prompt, so a trace shows what the model no longer sees."""

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.tool_loop_condensed_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.tool_loop_condensed_event.description"
    )

    loop: Annotated[str, Field(description="The blueprint's tool set the loop runs.")]
    tokens_before: Annotated[int, Field(description="The conversation's size before condensing.", ge=0)]
    tokens_after: Annotated[int, Field(description="The conversation's size after condensing.", ge=0)]
    condensed_results: Annotated[int, Field(description="How many earlier tool results were condensed.", ge=0)] = 0
    condensed_turns: Annotated[int, Field(description="How many earlier conversation turns were condensed.", ge=0)] = 0
    summary: Annotated[str, Field(description="What the condensed part now reads as, for the model.")] = ""
