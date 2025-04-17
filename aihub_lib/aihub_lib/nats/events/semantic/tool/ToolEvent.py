import json
from typing import Any, Dict, Optional, ClassVar

from openinference.semconv.trace import OpenInferenceSpanKindValues, SpanAttributes, ToolAttributes
from pydantic import Field

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.semantic.SemanticEvent import SemanticEvent


class ToolEvent(SemanticEvent):
    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.semantic_tool_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.semantic_tool_event.description")

    name: Optional[str] = Field(None, description="The name of the tool being utilized")
    description: Optional[str] = Field(None, description="Description of the tool's purpose and functionality")
    json_schema: Optional[Dict[str, Any]] = Field(None, description="The json schema of a tool input")
    parameters: Optional[Dict[str, Any]] = Field(None, description="The parameters definition for invoking the tool")

    def to_semantic_convention(self) -> Dict[str, str]:
        attributes = {
            SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.TOOL.value,
            SpanAttributes.TOOL_NAME: self.name,
            SpanAttributes.TOOL_DESCRIPTION: self.description,
            ToolAttributes.TOOL_JSON_SCHEMA: json.dumps(self.json_schema),
            SpanAttributes.TOOL_PARAMETERS: json.dumps(self.parameters),
        }
        return {k: v for k, v in attributes.items() if v is not None}
