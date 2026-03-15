import json
import logging
from typing import ClassVar

from aihub_lib.displayers.EventDisplayer import EventDisplayer
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.mcp.McpClientConfig import McpClientConfig
from aihub_lib.nats.events import StopEvent, UserMessageEvent
from llama_index.core.base.llms.types import ChatMessage, MessageRole

from aihub_agent.agents.Agent import Agent
from aihub_agent.context.run.RunContext import RunContext
from aihub_agent.mcp.McpClientFactory import McpClientFactory
from aihub_agent.mcp.McpToolService import McpToolService
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

        tool_schemas = McpToolService.to_openai_tool_schemas(tools)
        await run_context.set(TOOL_SCHEMAS_KEY, tool_schemas)

        return McpReasoningEvent(
            messages=[McpToolService.serialize_message(msg) for msg in event.messages],
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
        messages = [McpToolService.deserialize_message(m) for m in event.messages]
        tool_schemas = await run_context.get(TOOL_SCHEMAS_KEY)

        async with config.llm.cost_reporting_llm(displayer) as llm:
            response = await llm.achat(messages, tools=tool_schemas)

        assistant_msg = response.message
        tool_calls = assistant_msg.additional_kwargs.get("tool_calls", [])

        if not tool_calls:
            await displayer.display_chunk(str(assistant_msg.content), config.llm.model_name)
            print(response.message.content)
            return StopEvent()
        messages.append(assistant_msg)

        return McpToolCallEvent(
            tool_calls=[McpToolService.extract_tool_call_payload(tc) for tc in tool_calls],
            messages=[McpToolService.serialize_message(msg) for msg in messages],
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
        messages = [McpToolService.deserialize_message(m) for m in event.messages]

        async with McpClientFactory.create(mcp_config) as mcp_client:
            for tc in event.tool_calls:
                tool_name = tc["name"]
                arguments = tc["arguments"]

                await displayer.display_thought(f"Calling tool: {tool_name}({json.dumps(arguments)})")
                result = await mcp_client.call_tool(tool_name, arguments)

                messages.append(
                    ChatMessage(
                        role=MessageRole.TOOL,
                        content=McpToolService.extract_result_text(result),
                        additional_kwargs={"tool_call_id": tc["id"], "name": tool_name},
                    )
                )

        return McpReasoningEvent(
            messages=[McpToolService.serialize_message(msg) for msg in messages],
        )
