import json
from typing import Optional, Dict, Any

from openinference.semconv.trace import (
    SpanAttributes,
    ToolAttributes,
    OpenInferenceSpanKindValues,
)
from pydantic import Field

from lib_core.nats.events.semantic.SemanticEvent import SemanticEvent


class ToolEvent(SemanticEvent):
    name: Optional[str] = Field(None, description="The name of the tool being utilized")
    description: Optional[str] = Field(None, description="Description of the tool's purpose and functionality")
    json_schema: Optional[Dict[str, Any]] = Field(None, description="The json schema of a tool input")
    parameters: Optional[Dict[str, Any]] = Field(None, description="The parameters definition for invoking the tool")

    def to_semantic_convention(self) -> Dict[str, str]:
        return {
            SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.TOOL.value,
            SpanAttributes.TOOL_NAME: self.name,
            SpanAttributes.TOOL_DESCRIPTION: self.description,
            ToolAttributes.TOOL_JSON_SCHEMA: json.dumps(self.json_schema),
            SpanAttributes.TOOL_PARAMETERS: json.dumps(self.parameters),
        }
