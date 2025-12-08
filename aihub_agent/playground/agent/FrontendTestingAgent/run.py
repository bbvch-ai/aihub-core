# ruff: noqa: E402
from aihub_lib.infrastructure.opentelemetry.AihubInstrumentor import AihubInstrumentor  # isort: skip

AihubInstrumentor().instrument()

import asyncio

from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.logging.logger import enable_logging
from aihub_lib.infrastructure.nats.NatsSettings import NatsSettings
from aihub_lib.infrastructure.redis.RedisSettings import RedisSettings

from aihub_agent.runners.MultiprocessAgentRunner import MultiprocessAgentRunner
from playground.agent.FrontendTestingAgent.FrontendTestingAgent import FrontendTestingAgent
from playground.agent.FrontendTestingAgent.FrontendTestingAgentConfig import FrontendTestingAgentConfig

enable_logging()


async def main():
    runner = MultiprocessAgentRunner(
        servers=[NatsSettings().ENDPOINT],
        redis_url=RedisSettings().URL,
        agent_type=FrontendTestingAgent,
        agent_config=FrontendTestingAgentConfig(
            agent_id="frontend_testing",
            agent_class=FrontendTestingAgent.__name__,
            name=LocaleString(en="Frontend Testing Agent"),
            description=LocaleString(en="This is an agent that can be used to develop the frontend"),
            llm=LLMConfig(model_name="text-generation/mini"),
        ),
    )

    await runner.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
