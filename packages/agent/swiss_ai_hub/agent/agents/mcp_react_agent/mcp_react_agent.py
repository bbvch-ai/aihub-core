from typing import ClassVar

from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import (
    LLMStopEvent,
    Message,
    StopEvent,
    ToolEvent,
    UserMessageEvent,
)
from swiss_ai_hub.core.generative_ai import limit_chat_history
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.mcp.mcp_client_config import McpClientConfig

from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.agents.mcp_react_agent.configs.mcp_react_agent_config import McpReactAgentConfig
from swiss_ai_hub.agent.agents.mcp_react_agent.events.mcp_reasoning_event import McpReasoningEvent
from swiss_ai_hub.agent.context.run.run_context import RunContext
from swiss_ai_hub.agent.context.thread.thread_context import ThreadContext
from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString
from swiss_ai_hub.agent.mcp.mcp_auth_resolver import McpAuthResolver
from swiss_ai_hub.agent.mcp.mcp_client_factory import McpClientFactory
from swiss_ai_hub.agent.mcp.mcp_resource_schemas import fetch_static_resources, resource_read_tool_schema
from swiss_ai_hub.agent.mcp.mcp_tool_schemas import execute_single_tool_call, to_openai_tool_schemas, to_tool_events
from swiss_ai_hub.agent.workflow.decorators.precondition import precondition
from swiss_ai_hub.agent.workflow.decorators.step import step

TOOL_SCHEMAS_KEY = "mcp_tool_schemas"
CONVERSATION_KEY = "conversation"
TOTAL_TOOL_CALLS_KEY = "total_tool_calls"
NEW_TOOL_CALLS_KEY = "new_tool_calls"


@precondition()
async def within_max_iterations(reasoning_events: list[McpReasoningEvent], config: McpReactAgentConfig) -> bool:
    return len(reasoning_events) < config.max_iterations


@precondition()
async def exceeded_max_iterations(reasoning_events: list[McpReasoningEvent], config: McpReactAgentConfig) -> bool:
    return len(reasoning_events) >= config.max_iterations


@precondition()
async def all_tool_calls_emitted(tool_events: list[ToolEvent], run_context: RunContext) -> bool:
    total = await run_context.get(TOTAL_TOOL_CALLS_KEY, 0)
    return total > 0 and len(tool_events) == total


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
        """Discover MCP tools and resources, seed conversation with system prompt, trigger first reasoning iteration."""
        user_token = await McpAuthResolver.resolve_user_token(run_context)
        async with McpClientFactory.create(mcp_config, user_token=user_token) as mcp_client:
            tools = await mcp_client.list_tools()
            server_instructions = mcp_client.initialize_result.instructions if mcp_client.initialize_result else None

            server_supports_resources = (
                mcp_client.initialize_result is not None
                and mcp_client.initialize_result.capabilities.resources is not None
            )
            resource_context = await fetch_static_resources(mcp_client) if server_supports_resources else None
            resource_templates = await mcp_client.list_resource_templates() if server_supports_resources else []

        tool_schemas = to_openai_tool_schemas(tools)
        if resource_templates:
            tool_schemas.append(resource_read_tool_schema(resource_templates))
        await run_context.set(TOOL_SCHEMAS_KEY, tool_schemas)

        messages: list[ChatMessage] = []
        if config.system_prompt:
            locale = event.locale
            messages.append(ChatMessage(role=MessageRole.SYSTEM, content=config.system_prompt.in_locale(locale)))

        if server_instructions:
            messages.append(ChatMessage(role=MessageRole.SYSTEM, content=server_instructions))

        if resource_context:
            messages.append(ChatMessage(role=MessageRole.SYSTEM, content=resource_context))

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
        thread_context: ThreadContext,
        t: LocaleHandler,
    ) -> list[ToolEvent] | StopEvent:
        """Ask the LLM what to do next — call a tool or respond to the user."""
        chat_messages = [m.to_llama_index() for m in event.input_messages]
        tool_schemas = await run_context.get(TOOL_SCHEMAS_KEY)

        async with config.llm.cost_reporting_llm(displayer) as llm:
            response = await llm.achat(chat_messages, tools=tool_schemas)

        assistant = Message.from_llama_index(response.message)

        if not assistant.tool_calls:
            await displayer.display_chunk(assistant.content, config.llm.model_name)
            stop_event = LLMStopEvent(
                input_messages=event.input_messages,
                output_messages=[assistant],
                chat_model_name=config.llm.model_name,
            )
            # TEMP: conversation metadata (title + follow-up) generation disabled pending investigation.
            # Re-enable by restoring the call below and its `generate_conversation_metadata` import.
            # Inline, not a @step: the dispatcher won't dispatch steps waiting on a stop event. See ADR 2026_06_18.
            # await generate_conversation_metadata(stop_event.chat_messages, config.llm, displayer, t, thread_context)
            return stop_event

        await run_context.set(CONVERSATION_KEY, [m.model_dump() for m in [*event.input_messages, assistant]])

        previous_total = await run_context.get(TOTAL_TOOL_CALLS_KEY, 0)
        await run_context.set(TOTAL_TOOL_CALLS_KEY, previous_total + len(assistant.tool_calls))
        await run_context.set(NEW_TOOL_CALLS_KEY, len(assistant.tool_calls))

        return to_tool_events(assistant.tool_calls, tool_schemas)

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
        precondition=all_tool_calls_emitted,
    )
    async def tool_execution_step(
        self,
        tool_events: list[ToolEvent],
        mcp_config: McpClientConfig,
        run_context: RunContext,
    ) -> McpReasoningEvent:
        """Execute the requested tool calls on the MCP server and feed results back into the conversation."""
        conversation = [Message.model_validate(m) for m in await run_context.get(CONVERSATION_KEY)]
        new_count = await run_context.get(NEW_TOOL_CALLS_KEY)
        new_tool_events = tool_events[-new_count:]

        tool_messages: list[Message] = []
        user_token = await McpAuthResolver.resolve_user_token(run_context)
        async with McpClientFactory.create(mcp_config, user_token=user_token) as mcp_client:
            for tool_event in new_tool_events:
                message = await execute_single_tool_call(
                    mcp_client,
                    tool_call_id=tool_event.tool_call_id,
                    tool_name=tool_event.name,
                    arguments=tool_event.parameters,
                )
                tool_messages.append(message)

        return McpReasoningEvent(input_messages=[*conversation, *tool_messages])
