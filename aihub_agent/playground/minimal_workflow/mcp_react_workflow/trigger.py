"""One-shot test runner for the MCP ReAct Agent.

Requires:
- NATS running (default: nats://localhost:4222)
- Redis/Valkey running (default: redis://localhost:6379)
- MetaMCP running (default: http://localhost:12008)
- LiteLLM running (default: http://localhost:4000)

Usage:
    cd aihub_agent && poetry run python -m playground.minimal_workflow.mcp_react_workflow.trigger
"""

import asyncio

from aihub_lib.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthSettings import (
    DangerousDevelopmentOnlyAuthSettings,
)
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.logging.logger import enable_logging
from aihub_lib.mcp.McpHostConfig import McpConnectionConfig, McpHostConfig
from aihub_lib.nats.events import UserMessageEvent
from llama_index.core.base.llms.types import ChatMessage, MessageRole

from aihub_agent.runners.AgentTestRunner import AgentTestRunner
from playground.minimal_workflow.mcp_react_workflow.McpReactAgent import McpReactAgent
from playground.minimal_workflow.mcp_react_workflow.McpReactAgentConfig import McpReactAgentConfig

enable_logging()

# MetaMCP endpoint URL — adjust port/host if running differently
# Auth is disabled on the dev endpoint (bootstrap: enable_auth=false)
METAMCP_ENDPOINT = "http://localhost:12008/metamcp/default/mcp"

# LLM model — must be available in LiteLLM
LLM_MODEL = "text-generation/mini"

# User message to test with
USER_MESSAGE = "Use the sequential thinking tool to break down the problem: What are the 3 most important factors when designing a REST API?"


async def main() -> None:
    runner = AgentTestRunner(
        agent_type=McpReactAgent,
        agent_config=McpReactAgentConfig(
            agent_id="mcp_react_agent",
            agent_class=McpReactAgent.__name__,
            name=LocaleString(en="MCP ReAct Agent"),
            description=LocaleString(en="Demo agent with LLM-driven MCP tool calling"),
            mcp=McpHostConfig(
                connections=[
                    McpConnectionConfig(
                        name="metamcp-default",
                        url=METAMCP_ENDPOINT,
                        transport="streamable_http",
                    ),
                ],
            ),
            llm=LLMConfig(model_name=LLM_MODEL),
        ),
    )

    async with runner.test_run(delay_before_stop=30) as topic:
        await runner.send_event_from_topic(
            topic=topic,
            start_event=UserMessageEvent(
                messages=[ChatMessage(content=USER_MESSAGE, role=MessageRole.USER)],
                user=DangerousDevelopmentOnlyAuthSettings().get_user_identity(),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
