import asyncio

from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.logging.logger import enable_logging
from aihub_lib.infrastructure.nats.NatsSettings import NatsSettings
from aihub_lib.infrastructure.redis.RedisSettings import RedisSettings
from pydantic_settings import BaseSettings

from aihub_agent.agents.ExpertAskingAgent.ExpertAskingAgent import ExpertAskingAgent
from aihub_agent.agents.ExpertAskingAgent.ExpertAskingAgentConfig import ExpertAskingAgentConfig
from aihub_agent.runners.AgentRunner import AgentRunner

enable_logging()


class ExpertAskingAgentSettings(BaseSettings):
    """Settings for the ExpertAskingAgent loaded from environment variables."""

    EXPERT_CHANNEL_TYPE: str = "gui"
    SLACK_CHANNEL_ID: str | None = None
    EXPERT_GROUP: str | None = None
    INSIGHT_NAMESPACE: str = "default"
    INSIGHT_AGENT_CLASS: str | None = "InsightAgent"
    INSIGHT_AGENT_ID: str | None = "insight_agent"


async def main():
    settings = ExpertAskingAgentSettings()
    servers_list = [NatsSettings().ENDPOINT]
    runner = AgentRunner(
        agent_type=ExpertAskingAgent,
        default_agent_config=ExpertAskingAgentConfig(
            agent_class=ExpertAskingAgent.__name__,
            agent_id="expert_asking_agent",
            name=LocaleString(
                en="Expert Asking Agent",
                de="Experten-Anfrage Agent",
                fr="Agent de Demande d'Experts",
                it="Agente di Richiesta Esperti",
            ),
            description=LocaleString(
                en="Poses questions to human experts and validates their responses.",
                de="Stellt Fragen an menschliche Experten und validiert deren Antworten.",
                fr="Pose des questions aux experts humains et valide leurs réponses.",
                it="Pone domande agli esperti umani e valida le loro risposte.",
            ),
            llm=LLMConfig(model_name="text-generation/nano"),
            expert_channel_type=settings.EXPERT_CHANNEL_TYPE,  # type: ignore[arg-type]
            slack_channel_id=settings.SLACK_CHANNEL_ID,
            expert_group=settings.EXPERT_GROUP,
            loop_max=3,
            insight_namespace=settings.INSIGHT_NAMESPACE,
            insight_agent_class=settings.INSIGHT_AGENT_CLASS,
            insight_agent_id=settings.INSIGHT_AGENT_ID,
        ),
        redis_url=RedisSettings().URL,
        servers=servers_list,
    )

    await runner.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
