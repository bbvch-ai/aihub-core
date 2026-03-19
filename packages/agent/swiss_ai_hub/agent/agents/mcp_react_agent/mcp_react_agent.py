import json
from typing import ClassVar

from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import Message, StopEvent, ToolEvent, UserMessageEvent
from swiss_ai_hub.core.generative_ai import limit_chat_history
from swiss_ai_hub.core.mcp.mcp_client_config import McpClientConfig

from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.agents.mcp_react_agent.configs.mcp_react_agent_config import McpReactAgentConfig
from swiss_ai_hub.agent.agents.mcp_react_agent.events.mcp_reasoning_event import McpReasoningEvent
from swiss_ai_hub.agent.context.run.run_context import RunContext
from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString
from swiss_ai_hub.agent.mcp.mcp_client_factory import McpClientFactory
from swiss_ai_hub.agent.mcp.mcp_tool_schemas import execute_tool_calls, to_openai_tool_schemas
from swiss_ai_hub.agent.workflow.decorators.precondition import precondition
from swiss_ai_hub.agent.workflow.decorators.step import step

TOOL_SCHEMAS_KEY = "mcp_tool_schemas"
PENDING_TOOL_CALLS_KEY = "pending_tool_calls"
CONVERSATION_KEY = "conversation"


@precondition()
async def within_max_iterations(reasoning_events: list[McpReasoningEvent], config: McpReactAgentConfig) -> bool:
    return len(reasoning_events) < config.max_iterations


@precondition()
async def exceeded_max_iterations(reasoning_events: list[McpReasoningEvent], config: McpReactAgentConfig) -> bool:
    return len(reasoning_events) >= config.max_iterations


class McpReactAgent(Agent):
    """ReAct agent that discovers and calls tools on an external MCP server."""

    name: ClassVar[AgentLocaleString] = AgentLocaleString.from_i18n_path("agent.mcp_react_agent.metadata.name")
    description: ClassVar[AgentLocaleString] = AgentLocaleString.from_i18n_path(
        "agent.mcp_react_agent.metadata.description"
    )
    icon: ClassVar[str] = "mage:plug"

    @step(
        name=AgentLocaleString.from_i18n_path("agent.mcp_react_agent.steps.init.name"),
        description=AgentLocaleString.from_i18n_path("agent.mcp_react_agent.steps.init.description"),
        icon="mage:search",
    )
    async def init_step(
        self,
        event: UserMessageEvent,
        mcp_config: McpClientConfig,
        config: McpReactAgentConfig,
        run_context: RunContext,
    ) -> McpReasoningEvent:
        """Discover MCP tools, seed conversation with system prompt, trigger first reasoning iteration."""
        async with McpClientFactory.create(mcp_config) as mcp_client:
            tools = await mcp_client.list_tools()

        await run_context.set(TOOL_SCHEMAS_KEY, to_openai_tool_schemas(tools))

        messages: list[ChatMessage] = []
        if config.system_prompt:
            locale = event.locale
            messages.append(ChatMessage(role=MessageRole.SYSTEM, content=config.system_prompt.in_locale(locale)))

        messages.extend(msg for msg in event.messages if msg.role != MessageRole.SYSTEM)

        limited = limit_chat_history(
            chat_history=messages,
            number_of_input_tokens=config.number_of_input_tokens,
        )

        return McpReasoningEvent(
            input_messages=[Message.from_llama_index(msg) for msg in limited],
        )

    @step(
        name=AgentLocaleString.from_i18n_path("agent.mcp_react_agent.steps.reasoning.name"),
        description=AgentLocaleString.from_i18n_path("agent.mcp_react_agent.steps.reasoning.description"),
        icon="mage:light-bulb",
        precondition=within_max_iterations,
    )
    async def reasoning_step(
        self,
        event: McpReasoningEvent,
        config: McpReactAgentConfig,
        displayer: EventDisplayer,
        run_context: RunContext,
    ) -> ToolEvent | StopEvent:
        """Ask the LLM what to do next — call a tool or respond to the user."""
        chat_messages = [m.to_llama_index() for m in event.input_messages]
        tool_schemas = await run_context.get(TOOL_SCHEMAS_KEY)

        async with config.llm.cost_reporting_llm(displayer) as llm:
            response = await llm.achat(chat_messages, tools=tool_schemas)

        assistant = Message.from_llama_index(response.message)

        if not assistant.tool_calls:
            await displayer.display_chunk(assistant.content, config.llm.model_name)
            return StopEvent()

        await run_context.set(CONVERSATION_KEY, [m.model_dump() for m in [*event.input_messages, assistant]])
        await run_context.set(PENDING_TOOL_CALLS_KEY, assistant.tool_calls)

        first_call = assistant.tool_calls[0]
        function = first_call["function"]
        tool_name = function["name"]
        arguments = (
            json.loads(function["arguments"]) if isinstance(function["arguments"], str) else function["arguments"]
        )

        tool_description = next(
            (t["function"]["description"] for t in tool_schemas if t["function"]["name"] == tool_name),
            None,
        )

        return ToolEvent(
            name=tool_name,
            description=tool_description,
            parameters=arguments,
        )

    @step(
        name=AgentLocaleString.from_i18n_path("agent.mcp_react_agent.steps.max_iterations_reached.name"),
        description=AgentLocaleString.from_i18n_path("agent.mcp_react_agent.steps.max_iterations_reached.description"),
        icon="mage:stop-sign",
        precondition=exceeded_max_iterations,
    )
    async def max_iterations_reached_step(
        self,
        _: McpReasoningEvent,
        displayer: EventDisplayer,
    ) -> StopEvent:
        """Gracefully terminate when the maximum number of reasoning iterations is reached."""
        await displayer.display_thought("Maximum reasoning iterations reached — stopping.")
        return StopEvent()

    @step(
        name=AgentLocaleString.from_i18n_path("agent.mcp_react_agent.steps.tool_execution.name"),
        description=AgentLocaleString.from_i18n_path("agent.mcp_react_agent.steps.tool_execution.description"),
        icon="mage:wand",
    )
    async def tool_execution_step(
        self,
        _: ToolEvent,
        mcp_config: McpClientConfig,
        run_context: RunContext,
    ) -> McpReasoningEvent:
        """Execute the requested tool calls on the MCP server and feed results back into the conversation."""
        tool_calls = await run_context.get(PENDING_TOOL_CALLS_KEY)
        conversation = [Message.model_validate(m) for m in await run_context.get(CONVERSATION_KEY)]

        async with McpClientFactory.create(mcp_config) as mcp_client:
            tool_messages = await execute_tool_calls(mcp_client, tool_calls)

        return McpReasoningEvent(input_messages=[*conversation, *tool_messages])
