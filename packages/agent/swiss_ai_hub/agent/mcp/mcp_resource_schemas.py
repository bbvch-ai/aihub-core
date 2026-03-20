import logging
from typing import Any

from fastmcp import Client
from mcp.types import BlobResourceContents, ResourceTemplate, TextResourceContents

logger = logging.getLogger(__name__)

READ_MCP_RESOURCE_TOOL_NAME = "read_mcp_resource"


async def fetch_static_resources(mcp_client: Client) -> str | None:
    """List all static MCP resources and read their text contents into a formatted context string."""
    resources = await mcp_client.list_resources()
    if not resources:
        return None

    sections: list[str] = []
    for resource in resources:
        try:
            contents = await mcp_client.read_resource(str(resource.uri))
        except Exception:
            logger.warning("Failed to read MCP resource %s — skipping", resource.uri)
            continue

        text_parts = _extract_text(contents)
        if not text_parts:
            continue

        header = f"### {resource.name or resource.uri}"
        if resource.description:
            header += f"\n{resource.description}"
        sections.append(f"{header}\n\n{text_parts}")

    if not sections:
        return None

    return "## MCP Server Resources\n\n" + "\n\n".join(sections)


def resource_read_tool_schema(templates: list[ResourceTemplate]) -> dict[str, Any]:
    """Build an OpenAI function-calling schema for the read_mcp_resource meta-tool."""
    template_lines = [f"- `{t.uriTemplate}`: {t.description or t.name or 'No description'}" for t in templates]
    description = "Read a resource from the MCP server by URI. Available resource templates:\n" + "\n".join(
        template_lines
    )

    return {
        "type": "function",
        "function": {
            "name": READ_MCP_RESOURCE_TOOL_NAME,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": {
                    "uri": {
                        "type": "string",
                        "description": "The resource URI to read. Fill in template parameters as needed.",
                    },
                },
                "required": ["uri"],
            },
        },
    }


async def execute_resource_read(mcp_client: Client, uri: str) -> str:
    """Read an MCP resource by URI and return its text content."""
    contents = await mcp_client.read_resource(uri)
    return _extract_text(contents)


def _extract_text(contents: list[TextResourceContents | BlobResourceContents]) -> str:
    """Join text contents, warn on blobs."""
    parts: list[str] = []
    for item in contents:
        if isinstance(item, TextResourceContents):
            parts.append(item.text)
        elif isinstance(item, BlobResourceContents):
            logger.warning("Skipping binary resource content (uri=%s) — only text is supported", item.uri)
    return "\n".join(parts)
