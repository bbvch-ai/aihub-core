# ruff: noqa: E402
from aihub_lib.infrastructure.opentelemetry.AihubInstrumentor import AihubInstrumentor  # isort: skip

AihubInstrumentor().instrument()

import asyncio
import os

from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.logging.logger import enable_logging
from aihub_lib.infrastructure.nats.NatsSettings import NatsSettings
from aihub_lib.infrastructure.redis.RedisSettings import RedisSettings
from pydantic import SecretStr

from aihub_agent.agents.AgentDeveloperAgent.AgentDeveloperAgent import AgentDeveloperAgent
from aihub_agent.agents.AgentDeveloperAgent.configs.AgentDeveloperAgentConfig import AgentDeveloperAgentConfig
from aihub_agent.runners.AgentRunner import AgentRunner

enable_logging()


async def main():
    # Get OpenCode connection details from environment
    opencode_server_url = os.getenv("OPENCODE_SERVER_URL", "http://localhost:8081")
    opencode_token = os.getenv("OPENCODE_TOKEN", "default-token")
    opencode_timeout = int(os.getenv("OPENCODE_TIMEOUT", "300"))

    servers_list = [NatsSettings().ENDPOINT]
    runner = AgentRunner(
        agent_type=AgentDeveloperAgent,
        default_agent_config=AgentDeveloperAgentConfig(
            agent_class=AgentDeveloperAgent.__name__,
            agent_id="agent_developer",
            name=LocaleString(en="Agent Developer"),
            description=LocaleString(en="Meta-agent for building AI agents through chat interface using OpenCode"),
            llm=LLMConfig(model_name="text-generation/claude-3.5-sonnet"),
            opencode_server_url=opencode_server_url,
            opencode_token=SecretStr(opencode_token),
            opencode_timeout=opencode_timeout,
        ),
        redis_url=RedisSettings().URL,
        servers=servers_list,
    )

    await runner.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
