from typing import Annotated, Any, ClassVar

from pydantic import Field

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.ControlAndDisplayEvent import ControlAndDisplayEvent


class ToolOutputEvent(ControlAndDisplayEvent):
    """Event emitted when a tool execution completes successfully."""

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.tool_output_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.tool_output_event.description"
    )

    name: Annotated[str, Field(description="The name of the tool that was executed")]
    title: Annotated[str | None, Field(description="Human-readable title for the tool execution")] = None
    output: Annotated[str, Field(description="The output/result from the tool execution")]
    input: Annotated[dict[str, Any] | None, Field(description="The input parameters used for the tool")] = None
    duration: Annotated[float | None, Field(description="Execution duration in seconds")] = None
    metadata: Annotated[dict[str, Any] | None, Field(description="Additional metadata about the tool execution")] = None
