import logging
from typing import ClassVar

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.mcp.McpHostManager import McpHostManager
from aihub_lib.nats.events import StartEvent, StopEvent

from aihub_agent.agents.Agent import Agent
from aihub_agent.workflow.decorators.step import step
from playground.minimal_workflow.mcp_discovery_workflow.events.ToolDiscoveryEvent import ToolDiscoveryEvent

logger = logging.getLogger(__name__)


class McpDiscoveryAgent(Agent):
    """Demo agent that discovers MCP tools without an LLM.

    Flow: StartEvent → discover tools → report results → StopEvent
    """

    name: ClassVar[LocaleString] = LocaleString(
        en="MCP Discovery Agent",
        de="MCP Discovery Agent",
        fr="Agent MCP Discovery",
        it="Agente MCP Discovery",
    )
    description: ClassVar[LocaleString] = LocaleString(
        en="Demo agent that connects to MetaMCP and lists available tools",
        de="Demo-Agent der sich mit MetaMCP verbindet und verfügbare Tools auflistet",
        fr="Agent démo qui se connecte à MetaMCP et liste les outils disponibles",
        it="Agente demo che si connette a MetaMCP e elenca gli strumenti disponibili",
    )
    icon: ClassVar[str] = "mage:search"

    @step()
    async def discover_tools(self, event: StartEvent, mcp_host: McpHostManager) -> ToolDiscoveryEvent:
        """Connect to MCP servers and discover available tools."""
        mcp_tools = await mcp_host.list_all_tools()
        tool_names = [t.name for t in mcp_tools]
        logger.info("Discovered %d MCP tools: %s", len(mcp_tools), tool_names)
        return ToolDiscoveryEvent(tool_names=tool_names)

    @step()
    async def report_results(self, event: ToolDiscoveryEvent) -> StopEvent:
        """Format discovered tools into a human-readable summary."""
        if not event.tool_names:
            return StopEvent(result="No MCP tools discovered.")

        tool_list = "\n".join(f"  - {name}" for name in event.tool_names)
        summary = f"Discovered {len(event.tool_names)} MCP tool(s):\n{tool_list}"
        logger.info(summary)
        return StopEvent(result=summary)
