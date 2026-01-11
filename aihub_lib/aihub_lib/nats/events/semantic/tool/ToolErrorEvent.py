import json
from typing import Annotated, Any, ClassVar

from openinference.semconv.trace import OpenInferenceSpanKindValues, SpanAttributes, ToolAttributes
from pydantic import Field

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.semantic.SemanticEvent import SemanticEvent


class ToolErrorEvent(SemanticEvent):
    """
    Event emitted when a tool execution fails.

    This event represents an error or failure during tool invocation,
    typically from AI agents executing tools that encounter errors like
    failed tests, command errors, or other execution failures.

    The event is both:
    - A SemanticEvent (influences workflow, visible to user, and traced in Phoenix)
    - Compatible with OpenInference tool conventions for observability
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.tool_error_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.tool_error_event.description"
    )

    # Tool identity
    name: Annotated[str, Field(description="The name of the tool that failed")]
    title: Annotated[str | None, Field(description="Human-readable title for the tool execution")] = None

    # Error information
    error: Annotated[str, Field(description="The error message or output from the failed tool execution")]
    input: Annotated[dict[str, Any] | None, Field(description="The input parameters used for the tool")] = None

    # Execution metadata
    duration: Annotated[float | None, Field(description="Execution duration in seconds before failure")] = None
    metadata: Annotated[
        dict[str, Any] | None, Field(description="Additional metadata about the tool execution")
    ] = None

    def to_semantic_convention(self) -> dict[str, str]:
        """
        Convert to OpenInference semantic conventions for tool execution.

        Uses standard tool attributes for tracing in Arize Phoenix and other
        OpenInference-compatible observability tools.
        """
        attributes = {
            SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.TOOL.value,
            SpanAttributes.TOOL_NAME: self.name,
            SpanAttributes.TOOL_PARAMETERS: json.dumps(self.input) if self.input else None,
            # Custom attributes for tool errors
            "tool.error": self.error,
            "tool.title": self.title,
            "tool.duration": str(self.duration) if self.duration is not None else None,
            "tool.status": "error",
        }
        return {k: v for k, v in attributes.items() if v is not None}
