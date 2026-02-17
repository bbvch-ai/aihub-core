"""One-shot test runner for the MCP Discovery Agent.

Requires:
- NATS running (default: nats://localhost:4222)
- Redis/Valkey running (default: redis://localhost:6379)
- MetaMCP running (default: http://localhost:12008)

Usage:
    cd aihub_agent && poetry run python -m playground.minimal_workflow.mcp_discovery_workflow.trigger
"""

import asyncio

from aihub_lib.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthSettings import (
    DangerousDevelopmentOnlyAuthSettings,
)
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.logging.logger import enable_logging
from aihub_lib.mcp.McpHostConfig import McpConnectionConfig, McpHostConfig
from aihub_lib.nats.events import StartEvent

from aihub_agent.runners.AgentTestRunner import AgentTestRunner
from playground.minimal_workflow.mcp_discovery_workflow.McpDiscoveryAgent import McpDiscoveryAgent
from playground.minimal_workflow.mcp_discovery_workflow.McpDiscoveryAgentConfig import McpDiscoveryAgentConfig

enable_logging()

# MetaMCP endpoint URL — adjust port/host if running differently
# Auth is disabled on the dev endpoint (bootstrap: enable_auth=false)
METAMCP_ENDPOINT = "http://localhost:12008/metamcp/default/mcp"


async def main() -> None:
    runner = AgentTestRunner(
        agent_type=McpDiscoveryAgent,
        agent_config=McpDiscoveryAgentConfig(
            agent_id="mcp_discovery_agent",
            agent_class=McpDiscoveryAgent.__name__,
            name=LocaleString(en="MCP Discovery Agent"),
            description=LocaleString(en="Demo agent that discovers MCP tools"),
            mcp=McpHostConfig(
                connections=[
                    McpConnectionConfig(
                        name="metamcp-default",
                        url=METAMCP_ENDPOINT,
                        transport="streamable_http",
                    ),
                ],
            ),
        ),
    )

    async with runner.test_run() as topic:
        await runner.send_event_from_topic(
            topic=topic,
            start_event=StartEvent(
                user=DangerousDevelopmentOnlyAuthSettings().get_user_identity(),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
