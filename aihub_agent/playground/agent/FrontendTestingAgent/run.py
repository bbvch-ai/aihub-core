import asyncio

from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.nats.NatsConfig import NatsConfig
from aihub_lib.infrastructure.redis.RedisConfig import RedisConfig
from aihub_lib.testing.logging.logger import enable_logging

from aihub_agent.runners.MultiprocessAgentRunner import MultiprocessAgentRunner
from playground.agent.FrontendTestingAgent.FrontendTestingAgent import FrontendTestingAgent
from playground.agent.FrontendTestingAgent.FrontendTestingAgentConfig import FrontendTestingAgentConfig

enable_logging()


async def main():
    runner = MultiprocessAgentRunner(
        servers=[NatsConfig().NATS_ENDPOINT],
        redis_url=RedisConfig().REDIS_URL,
        agent_type=FrontendTestingAgent,
        agent_config=FrontendTestingAgentConfig(
            agent_id="frontend_testing",
            agent_class=FrontendTestingAgent.__name__,
            name=LocaleString(en="Frontend Testing Agent"),
            description=LocaleString(en="This is an agent that can be used to develop the frontend"),
            llm=LLMConfig(model_name="azure/gpt-4o-mini")
        ),
    )

    await runner.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
