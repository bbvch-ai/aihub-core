import asyncio

from aihub_lib.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthSettings import (
    DangerousDevelopmentOnlyAuthSettings,
)
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.logging.logger import enable_logging
from aihub_lib.mcp.McpClientConfig import McpClientConfig
from aihub_lib.nats.events import UserMessageEvent
from llama_index.core.base.llms.types import ChatMessage, MessageRole

from aihub_agent.runners.AgentTestRunner import AgentTestRunner
from playground.minimal_workflow.mcp_react_workflow.McpReactAgent import McpReactAgent
from playground.minimal_workflow.mcp_react_workflow.McpReactAgentConfig import McpReactAgentConfig

enable_logging()


async def main():
    runner = AgentTestRunner(
        agent_type=McpReactAgent,
        agent_config=McpReactAgentConfig(
            agent_id="mcp_react_agent",
            name=LocaleString(en="MCP React Agent"),
            description=LocaleString(en="Agent that calls external MCP tools"),
            mcp=McpClientConfig(name="test-tools", url="http://127.0.0.1:9090/mcp"),
            llm=LLMConfig(model_name="text-generation/Qwen3-VL-235B-A22B-Instruct"),
        ),
    )

    async with runner.test_run(delay_before_stop=60) as topic:
        await runner.send_event_from_topic(
            topic=topic,
            start_event=UserMessageEvent(
                messages=[ChatMessage(content="What is 17 + 25? Use the add tool.", role=MessageRole.USER)],
                user=DangerousDevelopmentOnlyAuthSettings().get_user_identity(),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
