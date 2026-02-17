"""Reusable utilities for LLM-driven tool calling with MCP and virtual agent tools.

Any agent that needs to combine MCP tools with LLM function calling can use these
functions instead of reimplementing the parsing and dispatching logic.
"""

import json
from typing import Annotated, Any

from llama_index.core.base.llms.types import ChatMessage, MessageRole
from mcp.types import Tool
from pydantic import BaseModel, Field

from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.mcp.tool_conversion import mcp_tool_to_openai_function


class ParsedToolCall(BaseModel):
    """A single tool call parsed from an LLM response."""

    tool_call_id: Annotated[str, Field(description="Unique ID assigned by the LLM to this tool call.")]
    tool_name: Annotated[str, Field(description="Name of the tool the LLM wants to invoke.")]
    arguments: Annotated[dict[str, Any], Field(description="Parsed arguments for the tool call.")]
    is_mcp: Annotated[bool, Field(description="Whether this call targets an MCP tool or a virtual agent tool.")]


def agent_tool_schema(tool_name: str, tool_description: str, parameters_schema: dict[str, Any]) -> dict[str, Any]:
    """Build a single OpenAI function-calling schema for a virtual tool.

    Use this to expose non-MCP capabilities (e.g. delegated agents) as tools
    that an LLM can invoke alongside real MCP tools.
    """
    return {
        "type": "function",
        "function": {
            "name": tool_name,
            "description": tool_description,
            "parameters": parameters_schema,
        },
    }


def build_tool_schemas(
    mcp_tools: list[Tool],
    additional_tool_schemas: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], set[str]]:
    """Combine MCP tools with additional pre-built OpenAI function schemas.

    Returns a tuple of (all_schemas, mcp_tool_names) so the caller can
    distinguish MCP tool calls from virtual tool calls.
    """
    schemas = [mcp_tool_to_openai_function(t) for t in mcp_tools]
    mcp_tool_names = {t.name for t in mcp_tools}
    schemas.extend(additional_tool_schemas)
    return schemas, mcp_tool_names


def parse_tool_calls(tool_calls: list[Any], mcp_tool_names: set[str]) -> list[ParsedToolCall]:
    """Parse raw LLM tool_calls (dict or OpenAI objects) into typed models."""
    parsed: list[ParsedToolCall] = []
    for tc in tool_calls:
        if isinstance(tc, dict):
            fn = tc["function"]
            tool_name = fn["name"]
            raw_args = fn["arguments"]
            parsed.append(
                ParsedToolCall(
                    tool_call_id=tc["id"],
                    tool_name=tool_name,
                    arguments=json.loads(raw_args) if isinstance(raw_args, str) else raw_args,
                    is_mcp=tool_name in mcp_tool_names,
                )
            )
        else:
            tool_name = tc.function.name
            raw_args = tc.function.arguments
            parsed.append(
                ParsedToolCall(
                    tool_call_id=tc.id,
                    tool_name=tool_name,
                    arguments=json.loads(raw_args) if isinstance(raw_args, str) else raw_args,
                    is_mcp=tool_name in mcp_tool_names,
                )
            )
    return parsed


def extract_mcp_result_text(result: Any) -> str:
    """Extract text from an MCP CallToolResult (fastmcp content blocks).

    Falls back to str(result) if the result doesn't have the expected
    content block structure.
    """
    if hasattr(result, "content"):
        return " ".join(str(block.text) for block in result.content if hasattr(block, "text"))
    return str(result)


def tool_result_message(tool_call_id: str, tool_name: str, result_text: str) -> ChatMessage:
    """Create a TOOL-role ChatMessage for appending to the conversation."""
    return ChatMessage(
        role=MessageRole.TOOL,
        content=result_text,
        additional_kwargs={"tool_call_id": tool_call_id, "name": tool_name},
    )


async def call_llm_with_tools(
    messages: list[ChatMessage],
    tool_schemas: list[dict[str, Any]],
    llm_config: LLMConfig,
) -> ChatMessage:
    """Call the LLM with tool schemas and return the assistant message."""
    llm, _ = llm_config.to_llama_index()
    response = await llm.achat(messages, tools=tool_schemas)
    return response.message
