import asyncio

from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.core.events.agent import UserMessageEvent
from swiss_ai_hub.core.generative_ai import LLMConfig
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.infrastructure import enable_logging
from swiss_ai_hub.core.mcp.mcp_client_config import McpClientConfig
from swiss_ai_hub.core.testing.auth_utils import fake_user

from playground.minimal_workflow.mcp_react_workflow.mcp_react_agent import McpReactAgent
from playground.minimal_workflow.mcp_react_workflow.mcp_react_agent_config import McpReactAgentConfig
from swiss_ai_hub.agent.runners import AgentTestRunner

enable_logging()


async def main():
    runner = AgentTestRunner(
        agent_type=McpReactAgent,
        agent_config=McpReactAgentConfig(
            agent_id="mcp_react_agent",
            name=LocaleString(en="MCP React Agent"),
            description=LocaleString(en="Agent that calls external MCP tools"),
            mcp=McpClientConfig(name="test-tools", url="http://127.0.0.1:9090/mcp"),
            llm=LLMConfig(model_name="text-generation/gemma-4-31B-it"),
        ),
    )

    async with runner.test_run(delay_before_stop=60) as topic:
        await runner.send_event_from_topic(
            topic=topic,
            start_event=UserMessageEvent(
                messages=[ChatMessage(content="What is 17 + 25? Use the add tool.", role=MessageRole.USER)],
                user=fake_user(),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
