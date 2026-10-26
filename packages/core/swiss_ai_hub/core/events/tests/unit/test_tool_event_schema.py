from typing import Annotated, Any, Self

from pydantic import BaseModel, Field

from swiss_ai_hub.core.events.agent.semantic.tool.tool_event import ToolEvent


class _Criteria(BaseModel):
    path_glob: Annotated[str | None, Field(description="Which paths")] = None


class _Selection(BaseModel):
    any_of: Annotated[list[_Criteria], Field(description="Alternatives")]
    first: _Criteria


class _Tree(BaseModel):
    children: list[Self] = []


def _keys(node: Any) -> set[str]:
    if isinstance(node, list):
        return {key for item in node for key in _keys(item)}
    if isinstance(node, dict):
        return set(node) | {key for value in node.values() for key in _keys(value)}
    return set()


def test_nested_models_are_inlined_without_dollar_keys():
    schema = {"$schema": "https://json-schema.org/draft/2020-12/schema", **_Selection.model_json_schema()}

    event = ToolEvent(name="select", json_schema=schema)

    assert not any(key.startswith("$") for key in _keys(event.model_dump()))
    assert event.json_schema["properties"]["any_of"]["items"]["properties"]["path_glob"]["description"] == "Which paths"
    assert event.json_schema["properties"]["any_of"]["description"] == "Alternatives"
    assert "path_glob" in event.json_schema["properties"]["first"]["properties"]


def test_a_recursive_model_ends_without_dollar_keys():
    event = ToolEvent(name="tree", json_schema=_Tree.model_json_schema())

    assert not any(key.startswith("$") for key in _keys(event.json_schema))


def test_a_flat_schema_is_unchanged():
    schema = {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}

    assert ToolEvent(name="search", json_schema=schema).json_schema == schema
