import json
from typing import Any

from llama_index.core.base.llms.types import ChatMessage, MessageRole
from mcp.types import Tool


class McpToolService:
    """Shared utilities for MCP tool-calling agents — schema conversion, message serialization, result extraction."""

    @staticmethod
    def to_openai_tool_schemas(tools: list[Tool]) -> list[dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": tool.inputSchema or {"type": "object", "properties": {}},
                },
            }
            for tool in tools
        ]

    @staticmethod
    def extract_tool_call_payload(tc: Any) -> dict[str, Any]:
        """Flatten a tool call for event payloads (id, name, arguments)."""
        if isinstance(tc, dict):
            return tc
        raw_args = tc.function.arguments
        return {
            "id": tc.id,
            "name": tc.function.name,
            "arguments": json.loads(raw_args) if isinstance(raw_args, str) else raw_args,
        }

    @staticmethod
    def _serialize_tool_call_for_openai(tc: Any) -> dict[str, Any]:
        """Preserve the full OpenAI tool call structure for LLM round-tripping."""
        if isinstance(tc, dict):
            if "function" in tc:
                return tc
            return {
                "id": tc["id"],
                "type": "function",
                "function": {"name": tc["name"], "arguments": json.dumps(tc["arguments"])},
            }
        raw_args = tc.function.arguments
        return {
            "id": tc.id,
            "type": "function",
            "function": {
                "name": tc.function.name,
                "arguments": raw_args if isinstance(raw_args, str) else json.dumps(raw_args),
            },
        }

    @staticmethod
    def serialize_message(msg: ChatMessage) -> dict[str, Any]:
        """Serialize a ChatMessage preserving the OpenAI tool call structure for LLM round-tripping."""
        data: dict[str, Any] = {"role": msg.role.value, "content": str(msg.content) if msg.content else ""}
        kwargs = msg.additional_kwargs
        if kwargs:
            safe_kwargs: dict[str, Any] = {}
            for k, v in kwargs.items():
                if k == "tool_calls":
                    safe_kwargs[k] = [McpToolService._serialize_tool_call_for_openai(tc) for tc in v]
                else:
                    safe_kwargs[k] = v
            data["additional_kwargs"] = safe_kwargs
        return data

    @staticmethod
    def deserialize_message(data: dict[str, Any]) -> ChatMessage:
        return ChatMessage(
            role=MessageRole(data["role"]),
            content=data.get("content", ""),
            additional_kwargs=data.get("additional_kwargs", {}),
        )

    @staticmethod
    def extract_result_text(result: Any) -> str:
        return " ".join(str(block.text) for block in result.content if hasattr(block, "text"))
