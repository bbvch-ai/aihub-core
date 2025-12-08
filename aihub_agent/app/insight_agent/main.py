import asyncio

from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.logging.logger import enable_logging
from aihub_lib.infrastructure.nats.NatsSettings import NatsSettings
from aihub_lib.infrastructure.redis.RedisSettings import RedisSettings
from pydantic_settings import BaseSettings

from aihub_agent.agents.InsightAgent.InsightAgent import InsightAgent
from aihub_agent.agents.InsightAgent.InsightAgentConfig import InsightAgentConfig
from aihub_agent.runners.AgentRunner import AgentRunner

enable_logging()


class InsightAgentSettings(BaseSettings):
    """Settings for the InsightAgent loaded from environment variables."""

    INSIGHT_NAMESPACE: str = "default"


async def main():
    settings = InsightAgentSettings()
    servers_list = [NatsSettings().ENDPOINT]
    runner = AgentRunner(
        agent_type=InsightAgent,
        default_agent_config=InsightAgentConfig(
            agent_class=InsightAgent.__name__,
            agent_id="insight_agent",
            name=LocaleString(
                en="Insight Agent",
                de="Insight Agent",
                fr="Agent d'Insights",
                it="Agente Insights",
            ),
            description=LocaleString(
                en="Extracts insights from expert conversations and stores them.",
                de="Extrahiert Erkenntnisse aus Expertengesprächen und speichert sie.",
                fr="Extrait des insights des conversations d'experts et les stocke.",
                it="Estrae insights dalle conversazioni con esperti e li memorizza.",
            ),
            llm=LLMConfig(model_name="text-generation/nano"),
            namespace=settings.INSIGHT_NAMESPACE,
        ),
        redis_url=RedisSettings().URL,
        servers=servers_list,
    )

    await runner.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
