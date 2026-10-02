from typing import Annotated, ClassVar

from llama_index.core.base.llms.types import ChatMessage
from pydantic import Field

from swiss_ai_hub.core.events.agent.control_and_display_event import ControlAndDisplayEvent
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class ToolResultEvent(ControlAndDisplayEvent):
    """What a tool call returned, for the model's next decision and, in gathering mode, the blueprint's answer."""

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.tool_result_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.tool_result_event.description"
    )

    tool_call_id: Annotated[str, Field(description="The call this result answers.")]
    name: Annotated[str, Field(description="The tool that ran.")]
    content: Annotated[str, Field(description="The result as the model reads it.")]
    block: Annotated[
        list[ChatMessage],
        Field(description="The result as context for an answer, when the tool renders it richer than its content."),
    ] = []
    is_error: Annotated[bool, Field(description="Whether the call failed or was declined.")] = False
