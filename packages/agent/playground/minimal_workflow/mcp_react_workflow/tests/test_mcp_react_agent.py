from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

from llama_index.core.base.llms.types import ChatMessage, ChatResponse, MessageRole
from mcp.types import TextContent, Tool
from pytest_bdd import given, scenarios, then, when
from swiss_ai_hub.core.events import BaseEvent
from swiss_ai_hub.core.events.agent import ToolEvent, UserMessageEvent
from swiss_ai_hub.core.generative_ai import LLMConfig
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.mcp.mcp_client_config import McpClientConfig
from swiss_ai_hub.core.testing import async_test
from swiss_ai_hub.core.testing.auth_utils import fake_user

from playground.minimal_workflow.mcp_react_workflow.mcp_react_agent import McpReactAgent
from playground.minimal_workflow.mcp_react_workflow.mcp_react_agent_config import McpReactAgentConfig
from swiss_ai_hub.agent.agents.mcp_react_agent.events.mcp_reasoning_event import McpReasoningEvent
from swiss_ai_hub.agent.runners import AgentTestRunner

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


def _make_mock_llm() -> AsyncMock:
    mock_llm = AsyncMock()
    mock_llm.achat = AsyncMock(side_effect=[_make_tool_call_response(), _make_text_response()])
    return mock_llm


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
    mock_mcp_client = AsyncMock()
    mock_mcp_client.list_tools = AsyncMock(return_value=[MOCK_TOOL])
    mock_mcp_client.call_tool = AsyncMock(
        return_value=MagicMock(content=[TextContent(type="text", text="hello")], is_error=False)
    )
    mock_mcp_client.initialize_result = None

    @asynccontextmanager
    async def fake_mcp_create(
        _config: McpClientConfig,
        user_token: str | None = None,  # noqa: ARG001
    ) -> AsyncIterator[AsyncMock]:
        yield mock_mcp_client

    mock_llm = _make_mock_llm()

    @asynccontextmanager
    async def fake_cost_reporting_llm(self, displayer) -> AsyncIterator[AsyncMock]:  # noqa: ARG001
        yield mock_llm

    with (
        patch("swiss_ai_hub.agent.mcp.mcp_client_factory.McpClientFactory.create", side_effect=fake_mcp_create),
        patch.object(LLMConfig, "cost_reporting_llm", fake_cost_reporting_llm),
    ):
        async with agent_runner.test_run() as topic:
            await agent_runner.send_event_from_topic(
                start_event=UserMessageEvent(
                    messages=[ChatMessage(content="Call echo", role=MessageRole.USER)],
                    user=fake_user(),
                ),
                topic=topic,
            )


@then("a StopEvent is present")
def _(agent_runner: AgentTestRunner):
    assert agent_runner.has_stop_event, "Agent did not complete"


def _deduplicate(events: list[BaseEvent]) -> list[BaseEvent]:
    """ControlAndDisplayEvents are observed twice (JetStream + NATS Core) — deduplicate by event_id."""
    return list({e.event_id: e for e in events}.values())


@then("a ToolEvent was emitted")
def _(agent_runner: AgentTestRunner):
    events = _deduplicate(agent_runner.get_events_of_class(ToolEvent))
    assert len(events) == 1, f"Expected exactly 1 ToolEvent, got {len(events)}"


@then("a McpReasoningEvent was emitted")
def _(agent_runner: AgentTestRunner):
    events = _deduplicate(agent_runner.get_events_of_class(McpReasoningEvent))
    assert len(events) == 2, f"Expected exactly 2 McpReasoningEvents (init + tool execution), got {len(events)}"
