from typing import Annotated, Any, ClassVar, Literal

from pydantic import Field

from swiss_ai_hub.core.events.agent.control_and_display_event import ControlAndDisplayEvent
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class ToolCallApprovedEvent(ControlAndDisplayEvent):
    """A tool call cleared to run, either because it needs no approval or because the user approved it.

    Function tools run in the loop itself; a capability tool's adapter step turns the call into the capability's own
    request, so the call runs the same sub-workflow, with the same events, as an explicit call would.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.tool_call_approved_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.tool_call_approved_event.description"
    )

    tool_call_id: Annotated[str, Field(description="The call's id, which its result answers.")]
    name: Annotated[str, Field(description="The tool to run.")]
    arguments: Annotated[dict[str, Any], Field(description="The arguments the model passed.")] = {}
    kind: Annotated[
        Literal["function", "capability"], Field(description="Whether the loop runs it or a capability does.")
    ]
    cite_sources: Annotated[bool, Field(description="Whether the tool tells the model to cite what it returns.")] = True
