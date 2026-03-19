import json
from typing import ClassVar

from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import Message, StopEvent, ToolEvent, UserMessageEvent
from swiss_ai_hub.core.mcp.mcp_client_config import McpClientConfig

from playground.minimal_workflow.mcp_react_workflow.events.mcp_reasoning_event import McpReasoningEvent
from playground.minimal_workflow.mcp_react_workflow.mcp_react_agent_config import McpReactAgentConfig
from swiss_ai_hub.agent.agents.agent import Agent
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
        """List MCP tools, seed conversation, trigger first reasoning iteration."""
        print(f"[McpReactAgent.init_step] Discovering tools on {mcp_config.url}")
        async with McpClientFactory.create(mcp_config) as mcp_client:
            tools = await mcp_client.list_tools()

        await run_context.set(TOOL_SCHEMAS_KEY, to_openai_tool_schemas(tools))

        return McpReasoningEvent(
            input_messages=[Message.from_llama_index(msg) for msg in event.messages],
        )

    @step(precondition=within_max_iterations)
    async def reasoning_step(
        self,
        event: McpReasoningEvent,
        config: McpReactAgentConfig,
        displayer: EventDisplayer,
        run_context: RunContext,
    ) -> ToolEvent | StopEvent:
        """Ask the LLM what to do next. Returns ToolEvent to continue or StopEvent to finish."""
        print("[McpReactAgent.reasoning_step]")
        chat_messages = [m.to_llama_index() for m in event.input_messages]
        tool_schemas = await run_context.get(TOOL_SCHEMAS_KEY)

        async with config.llm.cost_reporting_llm(displayer) as llm:
            response = await llm.achat(chat_messages, tools=tool_schemas)

        assistant = Message.from_llama_index(response.message)

        if not assistant.tool_calls:
            await displayer.display_chunk(assistant.content, config.llm.model_name)
            print(assistant.content)
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

    @step(precondition=exceeded_max_iterations)
    async def max_iterations_reached_step(
        self,
        _: McpReasoningEvent,
        displayer: EventDisplayer,
    ) -> StopEvent:
        """Gracefully terminate when the maximum number of reasoning iterations is reached."""
        await displayer.display_thought("Maximum reasoning iterations reached — stopping.")
        return StopEvent()

    @step()
    async def tool_execution_step(
        self,
        _: ToolEvent,
        mcp_config: McpClientConfig,
        run_context: RunContext,
    ) -> McpReasoningEvent:
        """Execute the requested tool calls and feed results back into the conversation."""
        print("[McpReactAgent.tool_execution_step]")
        tool_calls = await run_context.get(PENDING_TOOL_CALLS_KEY)
        conversation = [Message.model_validate(m) for m in await run_context.get(CONVERSATION_KEY)]

        async with McpClientFactory.create(mcp_config) as mcp_client:
            tool_messages = await execute_tool_calls(mcp_client, tool_calls)

        return McpReasoningEvent(input_messages=[*conversation, *tool_messages])
