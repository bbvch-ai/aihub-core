import json
import logging
from typing import ClassVar

from aihub_lib.displayers.EventDisplayer import EventDisplayer
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.mcp.McpClientConfig import McpClientConfig
from aihub_lib.nats.events import StopEvent, UserMessageEvent
from aihub_lib.nats.events.semantic.llm.Message import Message, TextContent
from mcp.types import TextContent as McpTextContent

from aihub_agent.agents.Agent import Agent
from aihub_agent.context.run.RunContext import RunContext
from aihub_agent.mcp.mcp_tool_schemas import to_openai_tool_schemas
from aihub_agent.mcp.McpClientFactory import McpClientFactory
from aihub_agent.workflow.decorators.step import step
from playground.minimal_workflow.mcp_react_workflow.events.McpReasoningEvent import McpReasoningEvent
from playground.minimal_workflow.mcp_react_workflow.events.McpToolCallEvent import McpToolCallEvent
from playground.minimal_workflow.mcp_react_workflow.McpReactAgentConfig import McpReactAgentConfig

logger = logging.getLogger(__name__)

TOOL_SCHEMAS_KEY = "mcp_tool_schemas"


class McpReactAgent(Agent):
    """ReAct agent — reasoning, tool execution, and loop decision are separate observable steps."""

    name: ClassVar[LocaleString] = LocaleString(
        en="MCP React Agent", de="MCP React Agent", fr="Agent MCP React", it="Agente MCP React"
    )
    description: ClassVar[LocaleString] = LocaleString(
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
            messages=[Message.from_llama_index(msg) for msg in event.messages],
        )

    @step(max_executions_per_run=50)
    async def reasoning_step(
        self,
        event: McpReasoningEvent,
        config: McpReactAgentConfig,
        displayer: EventDisplayer,
        run_context: RunContext,
    ) -> McpToolCallEvent | StopEvent:
        """Ask the LLM what to do next. Returns McpToolCallEvent to continue or StopEvent to finish.

        The loop is bounded by max_executions_per_run — if hit, the dispatcher silently skips
        this step and the run terminates without a StopEvent.
        """
        print("[McpReactAgent.reasoning_step]")
        chat_messages = [m.to_llama_index() for m in event.messages]
        tool_schemas = await run_context.get(TOOL_SCHEMAS_KEY)

        async with config.llm.cost_reporting_llm(displayer) as llm:
            response = await llm.achat(chat_messages, tools=tool_schemas)

        assistant = Message.from_llama_index(response.message)

        if not assistant.tool_calls:
            await displayer.display_chunk(assistant.content, config.llm.model_name)
            print(assistant.content)
            return StopEvent()

        return McpToolCallEvent(
            tool_calls=assistant.tool_calls,
            messages=[*event.messages, assistant],
        )

    @step(max_executions_per_run=50)
    async def tool_execution_step(
        self,
        event: McpToolCallEvent,
        mcp_config: McpClientConfig,
        displayer: EventDisplayer,
    ) -> McpReasoningEvent:
        """Execute the requested tool calls and feed results back into the conversation."""
        print("[McpReactAgent.tool_execution_step]")
        new_messages: list[Message] = []

        async with McpClientFactory.create(mcp_config) as mcp_client:
            for tool_call in event.tool_calls:
                function = tool_call["function"]
                tool_name = function["name"]
                arguments = (
                    json.loads(function["arguments"])
                    if isinstance(function["arguments"], str)
                    else function["arguments"]
                )

                await displayer.display_thought(f"Calling tool: {tool_name}({json.dumps(arguments)})")
                result = await mcp_client.call_tool(tool_name, arguments)
                result_text = " ".join(block.text for block in result.content if isinstance(block, McpTextContent))

                new_messages.append(
                    Message(
                        role="tool",
                        tool_call_id=tool_call["id"],
                        name=tool_name,
                        contents=[TextContent(text=result_text)],
                    )
                )

        return McpReasoningEvent(messages=[*event.messages, *new_messages])
