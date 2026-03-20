import json
from typing import Annotated, Any, ClassVar

from openinference.semconv.trace import OpenInferenceSpanKindValues, SpanAttributes, ToolAttributes
from pydantic import Field

from swiss_ai_hub.core.events.agent.semantic.semantic_event import SemanticEvent
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class ToolEvent(SemanticEvent):
    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.semantic_tool_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.semantic_tool_event.description"
    )

    tool_call_id: Annotated[
        str | None, Field(description="Unique identifier linking this invocation to its result")
    ] = None
    name: Annotated[str | None, Field(description="The name of the tool being utilized")] = None
    description: Annotated[str | None, Field(description="Description of the tool's purpose and functionality")] = None
    json_schema: Annotated[dict[str, Any] | None, Field(description="The json schema of a tool input")] = None
    parameters: Annotated[
        dict[str, Any] | None, Field(description="The parameters definition for invoking the tool")
    ] = None

    def to_semantic_convention(self) -> dict[str, str]:
        attributes = {
            SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.TOOL.value,
            SpanAttributes.TOOL_NAME: self.name,
            SpanAttributes.TOOL_DESCRIPTION: self.description,
            ToolAttributes.TOOL_JSON_SCHEMA: json.dumps(self.json_schema),
            SpanAttributes.TOOL_PARAMETERS: json.dumps(self.parameters),
        }
        return {k: v for k, v in attributes.items() if v is not None}
