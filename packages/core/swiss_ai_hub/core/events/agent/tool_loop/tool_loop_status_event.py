from typing import Annotated, ClassVar

from pydantic import Field

from swiss_ai_hub.core.events.agent.display.display_event import DisplayEvent
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class ToolLoopStatusEvent(DisplayEvent):
    """What the tool loop is doing while nothing else is visible: deciding in the background, or stopping early."""

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.tool_loop_status_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.tool_loop_status_event.description"
    )

    loop: Annotated[str, Field(description="The blueprint's tool set the loop runs.")]
    description: Annotated[str, Field(description="The status as users read it, in the run's locale.")]
    done: Annotated[bool, Field(description="Whether the step the status describes is over.")] = False
