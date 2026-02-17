"""One-shot test runner for the MCP Orchestrator Agent.

Requires:
- NATS running (default: nats://localhost:4222)
- Redis/Valkey running (default: redis://localhost:6379)
- MetaMCP running (default: http://localhost:12008)
- LiteLLM running (default: http://localhost:4000)

Usage:
    cd aihub_agent && poetry run python -m playground.minimal_workflow.mcp_orchestrator_workflow.trigger
"""

import asyncio

from aihub_lib.agents.AgentConfig import AgentConfig
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
from playground.minimal_workflow.mcp_orchestrator_workflow.McpOrchestratorAgent import McpOrchestratorAgent
from playground.minimal_workflow.mcp_orchestrator_workflow.McpOrchestratorAgentConfig import (
    DelegatedAgentToolConfig,
    McpOrchestratorAgentConfig,
)
from playground.minimal_workflow.mcp_orchestrator_workflow.MockKnowledgeBaseAgent import MockKnowledgeBaseAgent

enable_logging()

# MetaMCP endpoint URL — adjust port/host if running differently
# Auth is disabled on the dev endpoint (bootstrap: enable_auth=false)
METAMCP_ENDPOINT = "http://localhost:12008/metamcp/default/mcp"

# LLM model — must be available in LiteLLM
LLM_MODEL = "text-generation/mini"

# User message that should trigger both MCP tools and agent delegation
USER_MESSAGE = (
    "First, use the sequential thinking tool to analyze this question, "
    "then ask the knowledge base: What is the capital of Switzerland?"
)


async def main() -> None:
    worker_runner = AgentTestRunner(
        agent_type=MockKnowledgeBaseAgent,
        agent_config=AgentConfig(
            agent_id="knowledge_base_agent",
            agent_class=MockKnowledgeBaseAgent.__name__,
            name=LocaleString(en="Mock Knowledge Base Agent"),
            description=LocaleString(en="Returns hardcoded knowledge base results"),
        ),
    )

    orchestrator_runner = AgentTestRunner(
        agent_type=McpOrchestratorAgent,
        agent_config=McpOrchestratorAgentConfig(
            agent_id="mcp_orchestrator_agent",
            agent_class=McpOrchestratorAgent.__name__,
            name=LocaleString(en="MCP Orchestrator Agent"),
            description=LocaleString(en="Demo agent combining MCP tools with agent delegation"),
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
            delegated_agents=[
                DelegatedAgentToolConfig(
                    agent_id="knowledge_base_agent",
                    agent_class="MockKnowledgeBaseAgent",
                    tool_name="knowledge_base",
                    tool_description="Query the organization's knowledge base for factual information.",
                ),
            ],
        ),
    )

    async with worker_runner.test_run(delay_before_stop=30):
        async with orchestrator_runner.test_run(delay_before_stop=30) as topic:
            await orchestrator_runner.send_event_from_topic(
                topic=topic,
                start_event=UserMessageEvent(
                    messages=[ChatMessage(content=USER_MESSAGE, role=MessageRole.USER)],
                    user=DangerousDevelopmentOnlyAuthSettings().get_user_identity(),
                ),
            )


if __name__ == "__main__":
    asyncio.run(main())
