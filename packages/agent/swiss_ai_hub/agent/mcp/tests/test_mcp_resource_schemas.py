from unittest.mock import AsyncMock

import pytest
from mcp.types import BlobResourceContents, Resource, ResourceTemplate, TextResourceContents
from pydantic import AnyUrl

from swiss_ai_hub.agent.mcp.mcp_resource_schemas import (
    READ_MCP_RESOURCE_TOOL_NAME,
    execute_resource_read,
    fetch_static_resources,
    resource_read_tool_schema,
)


def _url(s: str) -> AnyUrl:
    return AnyUrl(s)


def _resource(uri: str, name: str, description: str | None = None) -> Resource:
    return Resource(uri=_url(uri), name=name, description=description)


def _template(uri_template: str, name: str, description: str | None = None) -> ResourceTemplate:
    return ResourceTemplate(uriTemplate=uri_template, name=name, description=description)


def _text_content(uri: str, text: str) -> TextResourceContents:
    return TextResourceContents(uri=_url(uri), text=text)


def _blob_content(uri: str, blob: str) -> BlobResourceContents:
    return BlobResourceContents(uri=_url(uri), blob=blob)


class TestFetchStaticResources:
    @pytest.mark.asyncio
    async def test_returns_none_when_no_resources(self):
        client = AsyncMock()
        client.list_resources = AsyncMock(return_value=[])
        assert await fetch_static_resources(client) is None

    @pytest.mark.asyncio
    async def test_formats_single_text_resource(self):
        client = AsyncMock()
        client.list_resources = AsyncMock(return_value=[_resource("config://app", "App Config")])
        client.read_resource = AsyncMock(return_value=[_text_content("config://app", "key=value")])

        result = await fetch_static_resources(client)

        assert result is not None
        assert "## MCP Server Resources" in result
        assert "### App Config" in result
        assert "key=value" in result

    @pytest.mark.asyncio
    async def test_includes_resource_description(self):
        client = AsyncMock()
        client.list_resources = AsyncMock(
            return_value=[_resource("config://app", "App Config", "Application settings")]
        )
        client.read_resource = AsyncMock(return_value=[_text_content("config://app", "data")])

        result = await fetch_static_resources(client)

        assert "Application settings" in result

    @pytest.mark.asyncio
    async def test_skips_blob_content(self):
        client = AsyncMock()
        client.list_resources = AsyncMock(return_value=[_resource("file://img", "Image")])
        client.read_resource = AsyncMock(return_value=[_blob_content("file://img", "base64data")])

        result = await fetch_static_resources(client)

        assert result is None

    @pytest.mark.asyncio
    async def test_skips_failed_reads(self):
        client = AsyncMock()
        client.list_resources = AsyncMock(
            return_value=[
                _resource("config://good", "Good"),
                _resource("config://bad", "Bad"),
            ]
        )
        client.read_resource = AsyncMock(
            side_effect=[
                [_text_content("config://good", "good data")],
                Exception("connection error"),
            ]
        )

        result = await fetch_static_resources(client)

        assert result is not None
        assert "good data" in result
        assert "Bad" not in result

    @pytest.mark.asyncio
    async def test_multiple_resources(self):
        client = AsyncMock()
        client.list_resources = AsyncMock(
            return_value=[
                _resource("config://a", "Config A"),
                _resource("config://b", "Config B"),
            ]
        )
        client.read_resource = AsyncMock(
            side_effect=[
                [_text_content("config://a", "data-a")],
                [_text_content("config://b", "data-b")],
            ]
        )

        result = await fetch_static_resources(client)

        assert "Config A" in result
        assert "data-a" in result
        assert "Config B" in result
        assert "data-b" in result


class TestResourceReadToolSchema:
    def test_generates_valid_openai_schema(self):
        templates = [_template("users://{id}/profile", "User Profile", "Get user profile")]
        schema = resource_read_tool_schema(templates)

        assert schema["type"] == "function"
        assert schema["function"]["name"] == READ_MCP_RESOURCE_TOOL_NAME
        assert "uri" in schema["function"]["parameters"]["properties"]
        assert "uri" in schema["function"]["parameters"]["required"]

    def test_includes_template_uris_in_description(self):
        templates = [
            _template("users://{id}/profile", "User Profile", "Get user profile"),
            _template("weather://{city}/current", "Weather", "Current weather"),
        ]
        schema = resource_read_tool_schema(templates)
        description = schema["function"]["description"]

        assert "users://{id}/profile" in description
        assert "weather://{city}/current" in description
        assert "Get user profile" in description
        assert "Current weather" in description

    def test_handles_template_without_description(self):
        templates = [_template("data://{key}", "Data")]
        schema = resource_read_tool_schema(templates)
        description = schema["function"]["description"]

        assert "data://{key}" in description
        assert "Data" in description


class TestExecuteResourceRead:
    @pytest.mark.asyncio
    async def test_reads_text_resource(self):
        client = AsyncMock()
        client.read_resource = AsyncMock(return_value=[_text_content("users://1/profile", "name=Alice")])

        result = await execute_resource_read(client, "users://1/profile")

        assert result == "name=Alice"
        client.read_resource.assert_awaited_once_with("users://1/profile")

    @pytest.mark.asyncio
    async def test_joins_multiple_text_contents(self):
        client = AsyncMock()
        client.read_resource = AsyncMock(
            return_value=[
                _text_content("data://multi", "line1"),
                _text_content("data://multi", "line2"),
            ]
        )

        result = await execute_resource_read(client, "data://multi")

        assert result == "line1\nline2"

    @pytest.mark.asyncio
    async def test_returns_empty_string_for_empty_content(self):
        client = AsyncMock()
        client.read_resource = AsyncMock(return_value=[])

        result = await execute_resource_read(client, "data://empty")

        assert result == ""
