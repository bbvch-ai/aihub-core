from typing import Annotated, Any, ClassVar

from pydantic import Field

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.ControlAndDisplayEvent import ControlAndDisplayEvent


class ToolErrorEvent(ControlAndDisplayEvent):
    """Event emitted when a tool execution fails."""

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.tool_error_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.tool_error_event.description"
    )

    name: Annotated[str, Field(description="The name of the tool that failed")]
    title: Annotated[str | None, Field(description="Human-readable title for the tool execution")] = None
    error: Annotated[str, Field(description="The error message or output from the failed tool execution")]
    input: Annotated[dict[str, Any] | None, Field(description="The input parameters used for the tool")] = None
    duration: Annotated[float | None, Field(description="Execution duration in seconds before failure")] = None
    metadata: Annotated[dict[str, Any] | None, Field(description="Additional metadata about the tool execution")] = None
