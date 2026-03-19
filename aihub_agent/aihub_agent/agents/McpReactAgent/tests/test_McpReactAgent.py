from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

from aihub_lib.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthSettings import (
    DangerousDevelopmentOnlyAuthSettings,
)
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.mcp.McpClientConfig import McpClientConfig
from aihub_lib.nats.events import UserMessageEvent
from aihub_lib.nats.events.BaseEvent import BaseEvent
from aihub_lib.nats.events.semantic.tool.ToolEvent import ToolEvent
from aihub_lib.testing.asyncio_utils.bdd import async_test
from llama_index.core.base.llms.types import ChatMessage, ChatResponse, MessageRole
from mcp.types import TextContent, Tool
from pytest_bdd import given, scenarios, then, when

from aihub_agent.agents.McpReactAgent.configs.McpReactAgentConfig import McpReactAgentConfig
from aihub_agent.agents.McpReactAgent.events.McpReasoningEvent import McpReasoningEvent
from aihub_agent.agents.McpReactAgent.McpReactAgent import McpReactAgent
from aihub_agent.runners.AgentTestRunner import AgentTestRunner

scenarios("./features/mcp_react_agent.feature")

MOCK_TOOL = Tool(name="echo", description="Echoes input", inputSchema={"type": "object", "properties": {}})


def _make_tool_call_response() -> ChatResponse:
    tool_call = MagicMock()
    tool_call.id = "call_1"
    tool_call.function.name = "echo"
    tool_call.function.arguments = "{}"
    return ChatResponse(
        message=ChatMessage(
            role=MessageRole.ASSISTANT,
            content="",
            additional_kwargs={"tool_calls": [tool_call]},
        )
    )


def _make_text_response() -> ChatResponse:
    return ChatResponse(
        message=ChatMessage(
            role=MessageRole.ASSISTANT,
            content="The echo tool returned: hello",
        )
    )


def _deduplicate(events: list[BaseEvent]) -> list[BaseEvent]:
    """ControlAndDisplayEvents are observed twice (JetStream + NATS Core) — deduplicate by event_id."""
    return list({e.event_id: e for e in events}.values())


@asynccontextmanager
async def _fake_mcp_create(_config: McpClientConfig) -> AsyncIterator[AsyncMock]:
    mock_mcp_client = AsyncMock()
    mock_mcp_client.list_tools = AsyncMock(return_value=[MOCK_TOOL])
    mock_mcp_client.call_tool = AsyncMock(
        return_value=MagicMock(content=[TextContent(type="text", text="hello")], is_error=False)
    )
    yield mock_mcp_client


@given("a McpReactAgent runner with a mocked MCP server and LLM", target_fixture="agent_runner")
def _():
    return AgentTestRunner(
        agent_type=McpReactAgent,
        agent_config=McpReactAgentConfig(
            agent_id="mcp_react_agent",
            name=LocaleString(en="MCP React Agent"),
            description=LocaleString(en="Test agent"),
            mcp=McpClientConfig(name="mock", url="http://mock-server/mcp"),
            llm=LLMConfig(model_name="text-generation/gpt-oss-120b"),
        ),
    )


@when("the start event is sent")
@async_test
async def _(agent_runner: AgentTestRunner):
    mock_llm = AsyncMock()
    mock_llm.achat = AsyncMock(side_effect=[_make_tool_call_response(), _make_text_response()])

    @asynccontextmanager
    async def fake_cost_reporting_llm(self, displayer) -> AsyncIterator[AsyncMock]:  # noqa: ARG001
        yield mock_llm

    with (
        patch("aihub_agent.mcp.McpClientFactory.McpClientFactory.create", side_effect=_fake_mcp_create),
        patch.object(LLMConfig, "cost_reporting_llm", fake_cost_reporting_llm),
    ):
        async with agent_runner.test_run() as topic:
            await agent_runner.send_event_from_topic(
                start_event=UserMessageEvent(
                    messages=[ChatMessage(content="Call echo", role=MessageRole.USER)],
                    user=DangerousDevelopmentOnlyAuthSettings().get_user_identity(),
                ),
                topic=topic,
            )


@then("a StopEvent is present")
def _(agent_runner: AgentTestRunner):
    assert agent_runner.has_stop_event, "Agent did not complete"


@then("a ToolEvent was emitted")
def _(agent_runner: AgentTestRunner):
    events = _deduplicate(agent_runner.get_events_of_class(ToolEvent))
    assert len(events) == 1, f"Expected exactly 1 ToolEvent, got {len(events)}"


@then("a McpReasoningEvent was emitted")
def _(agent_runner: AgentTestRunner):
    events = _deduplicate(agent_runner.get_events_of_class(McpReasoningEvent))
    assert len(events) == 2, f"Expected exactly 2 McpReasoningEvents (init + tool execution), got {len(events)}"
