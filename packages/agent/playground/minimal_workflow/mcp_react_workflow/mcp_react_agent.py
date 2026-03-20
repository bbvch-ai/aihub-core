from typing import ClassVar

from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import LLMStopEvent, Message, StopEvent, ToolEvent, UserMessageEvent
from swiss_ai_hub.core.mcp.mcp_client_config import McpClientConfig

from playground.minimal_workflow.mcp_react_workflow.events.mcp_reasoning_event import McpReasoningEvent
from playground.minimal_workflow.mcp_react_workflow.mcp_react_agent_config import McpReactAgentConfig
from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.context.run.run_context import RunContext
from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString
from swiss_ai_hub.agent.mcp.mcp_client_factory import McpClientFactory
from swiss_ai_hub.agent.mcp.mcp_resource_schemas import fetch_static_resources, resource_read_tool_schema
from swiss_ai_hub.agent.mcp.mcp_tool_schemas import execute_single_tool_call, to_openai_tool_schemas, to_tool_events
from swiss_ai_hub.agent.workflow.decorators.precondition import precondition
from swiss_ai_hub.agent.workflow.decorators.step import step

TOOL_SCHEMAS_KEY = "mcp_tool_schemas"
CONVERSATION_KEY = "conversation"
TOTAL_TOOL_CALLS_KEY = "total_tool_calls"


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
    """ReAct agent — reasoning, tool execution, and loop decision are separate observable steps."""

    name: ClassVar[AgentLocaleString] = AgentLocaleString(
        en="MCP React Agent", de="MCP React Agent", fr="Agent MCP React", it="Agente MCP React"
    )
    description: ClassVar[AgentLocaleString] = AgentLocaleString(
        en="Calls tools on external MCP servers",
        de="Ruft Tools auf externen MCP-Servern auf",
        fr="Appelle des outils sur des serveurs MCP externes",
        it="Chiama strumenti su server MCP esterni",
    )
    icon: ClassVar[str] = "mage:plug"

    @step()
    async def init_step(
        self,
        event: UserMessageEvent,
        mcp_config: McpClientConfig,
        run_context: RunContext,
    ) -> McpReasoningEvent:
        """List MCP tools and resources, seed conversation, trigger first reasoning iteration."""
        print(f"[init_step] Discovering tools and resources on {mcp_config.url}")
        async with McpClientFactory.create(mcp_config) as mcp_client:
            tools = await mcp_client.list_tools()
            print(f"[init_step] Tools: {[t.name for t in tools]}")

            server_supports_resources = (
                mcp_client.initialize_result is not None
                and mcp_client.initialize_result.capabilities.resources is not None
            )

            if server_supports_resources:
                resource_context = await fetch_static_resources(mcp_client)
                resource_templates = await mcp_client.list_resource_templates()
                print(
                    f"[init_step] Static resources: {resource_context is not None}, "
                    f"templates: {[t.uriTemplate for t in resource_templates]}"
                )
            else:
                resource_context = None
                resource_templates = []
                print("[init_step] Server does not support resources")

        tool_schemas = to_openai_tool_schemas(tools)
        if resource_templates:
            tool_schemas.append(resource_read_tool_schema(resource_templates))
        await run_context.set(TOOL_SCHEMAS_KEY, tool_schemas)

        input_messages = list(event.messages)
        if resource_context:
            from llama_index.core.base.llms.types import ChatMessage, MessageRole

            input_messages.insert(0, ChatMessage(role=MessageRole.SYSTEM, content=resource_context))

        return McpReasoningEvent(
            input_messages=[Message.from_llama_index(msg) for msg in input_messages],
        )

    @step(precondition=within_max_iterations)
    async def reasoning_step(
        self,
        event: McpReasoningEvent,
        config: McpReactAgentConfig,
        displayer: EventDisplayer,
        run_context: RunContext,
    ) -> list[ToolEvent] | StopEvent:
        """Ask the LLM what to do next. Returns ToolEvents to continue or StopEvent to finish."""
        print("[reasoning_step] LLM deciding next action...")
        chat_messages = [m.to_llama_index() for m in event.input_messages]
        tool_schemas = await run_context.get(TOOL_SCHEMAS_KEY)

        async with config.llm.cost_reporting_llm(displayer) as llm:
            response = await llm.achat(chat_messages, tools=tool_schemas)

        assistant = Message.from_llama_index(response.message)

        if not assistant.tool_calls:
            print(f"[reasoning_step] Final response: {assistant.content[:200]}")
            await displayer.display_chunk(assistant.content, config.llm.model_name)
            return LLMStopEvent(
                input_messages=event.input_messages,
                output_messages=[assistant],
                chat_model_name=config.llm.model_name,
            )

        for tc in assistant.tool_calls:
            fn = tc["function"]
            print(f"[reasoning_step] Calling: {fn['name']}({fn['arguments']})")

        await run_context.set(CONVERSATION_KEY, [m.model_dump() for m in [*event.input_messages, assistant]])

        previous_total = await run_context.get(TOTAL_TOOL_CALLS_KEY, 0)
        await run_context.set(TOTAL_TOOL_CALLS_KEY, previous_total + len(assistant.tool_calls))

        return to_tool_events(assistant.tool_calls, tool_schemas)

    @step(precondition=exceeded_max_iterations)
    async def max_iterations_reached_step(
        self,
        _: McpReasoningEvent,
        displayer: EventDisplayer,
    ) -> StopEvent:
        """Gracefully terminate when the maximum number of reasoning iterations is reached."""
        await displayer.display_thought("Maximum reasoning iterations reached — stopping.")
        return StopEvent()

    @step(precondition=all_tool_calls_emitted)
    async def tool_execution_step(
        self,
        tool_events: list[ToolEvent],
        mcp_config: McpClientConfig,
        run_context: RunContext,
    ) -> McpReasoningEvent:
        """Execute the requested tool calls and feed results back into the conversation."""
        print("[tool_execution_step] Executing tool calls")
        conversation = [Message.model_validate(m) for m in await run_context.get(CONVERSATION_KEY)]
        new_count = len(conversation[-1].tool_calls)
        new_tool_events = tool_events[-new_count:]

        tool_messages: list[Message] = []
        async with McpClientFactory.create(mcp_config) as mcp_client:
            for tool_event in new_tool_events:
                print(f"[tool_execution_step] {tool_event.name}({tool_event.parameters})")
                message = await execute_single_tool_call(
                    mcp_client,
                    tool_call_id=tool_event.tool_call_id,
                    tool_name=tool_event.name,
                    arguments=tool_event.parameters,
                )
                print(f"[tool_execution_step] -> {message.content[:200]}")
                tool_messages.append(message)

        return McpReasoningEvent(input_messages=[*conversation, *tool_messages])
