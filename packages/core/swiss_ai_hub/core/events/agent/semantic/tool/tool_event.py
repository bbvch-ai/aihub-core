import json
from typing import Annotated, Any, ClassVar

from openinference.semconv.trace import OpenInferenceSpanKindValues, SpanAttributes, ToolAttributes
from pydantic import Field, field_validator

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
    label: Annotated[
        str | None, Field(description="The tool's name as users read it, in the run's locale; the name otherwise")
    ] = None
    json_schema: Annotated[dict[str, Any] | None, Field(description="The json schema of a tool input")] = None
    parameters: Annotated[
        dict[str, Any] | None, Field(description="The parameters definition for invoking the tool")
    ] = None

    @field_validator("json_schema")
    @classmethod
    def _without_references(cls, schema: dict[str, Any] | None) -> dict[str, Any] | None:
        """Inlines `$defs` and drops other `$` keys: MongoDB rejects keys starting with '$', and a tool taking a
        nested model has them, so the persisted event would be refused."""
        if not schema:
            return schema
        return cls._inlined(schema, schema.get("$defs", {}), frozenset())

    @classmethod
    def _inlined(cls, node: Any, definitions: dict[str, Any], expanding: frozenset[str]) -> Any:
        if isinstance(node, list):
            return [cls._inlined(item, definitions, expanding) for item in node]
        if not isinstance(node, dict):
            return node
        name = str(node.get("$ref", "")).removeprefix("#/$defs/")
        if name in definitions and name not in expanding:
            merged = {**definitions[name], **{key: value for key, value in node.items() if key != "$ref"}}
            return cls._inlined(merged, definitions, expanding | {name})
        return {
            key: cls._inlined(value, definitions, expanding) for key, value in node.items() if not key.startswith("$")
        }

    def to_semantic_convention(self) -> dict[str, str]:
        attributes = {
            SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.TOOL.value,
            SpanAttributes.TOOL_NAME: self.name,
            SpanAttributes.TOOL_DESCRIPTION: self.description,
            ToolAttributes.TOOL_JSON_SCHEMA: json.dumps(self.json_schema),
            SpanAttributes.TOOL_PARAMETERS: json.dumps(self.parameters),
        }
        return {k: v for k, v in attributes.items() if v is not None}
