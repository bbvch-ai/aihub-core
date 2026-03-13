from typing import ClassVar

from aihub_lib.displayers.EventDisplayer import EventDisplayer
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.mcp.McpClientConfig import McpClientConfig
from aihub_lib.nats.events import StopEvent, UserMessageEvent

from aihub_agent.agents.Agent import Agent
from aihub_agent.mcp.McpClientFactory import McpClientFactory
from aihub_agent.mcp.McpReactService import McpReactService
from aihub_agent.workflow.decorators.step import step
from playground.minimal_workflow.mcp_react_workflow.McpReactAgentConfig import McpReactAgentConfig


class McpReactAgent(Agent):
    """ReAct agent — LLM reasons about which MCP tools to call, executes them, and iterates until it has an answer."""

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
    async def react_step(
        self,
        event: UserMessageEvent,
        mcp_config: McpClientConfig,
        config: McpReactAgentConfig,
        displayer: EventDisplayer,
    ) -> StopEvent:
        async with McpClientFactory.create(mcp_config) as mcp_client:
            async with config.llm.cost_reporting_llm(displayer) as llm:
                content = await McpReactService.react_loop(
                    mcp_client,
                    list(event.messages),
                    llm,
                    displayer,
                    config.llm.model_name,
                    config.max_iterations,
                )
        return StopEvent()
