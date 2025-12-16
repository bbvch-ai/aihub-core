import asyncio
import os

from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.logging.logger import enable_logging
from aihub_lib.infrastructure.nats.NatsSettings import NatsSettings
from aihub_lib.infrastructure.redis.RedisSettings import RedisSettings
from aihub_lib.nats.events.bot_in_the_loop.request.BotInTheLoopRequestEvent import SlackConfig, TeamsConfig

from aihub_agent.agents.ExpertAskingAgent.ExpertAskingAgent import ExpertAskingAgent
from aihub_agent.agents.ExpertAskingAgent.ExpertAskingAgentConfig import ExpertAskingAgentConfig
from aihub_agent.runners.AgentRunner import AgentRunner

enable_logging()


def get_channel_config() -> TeamsConfig | SlackConfig:
    """Build channel configuration from environment variables."""
    channel_type = os.environ.get("EXPERT_ASKING_CHANNEL_TYPE", "teams").lower()

    if channel_type == "slack":
        return SlackConfig(
            channel_id=os.environ["SLACK_CHANNEL_ID"],
            service_url=os.environ.get("SLACK_SERVICE_URL", "https://slack.botframework.com"),
        )
    else:
        return TeamsConfig(
            channel_id=os.environ["TEAMS_CHANNEL_ID"],
            tenant_id=os.environ["TEAMS_TENANT_ID"],
            bot_id=os.environ["TEAMS_BOT_ID"],
        )


async def main():
    servers_list = [NatsSettings().ENDPOINT]
    runner = AgentRunner(
        agent_type=ExpertAskingAgent,
        default_agent_config=ExpertAskingAgentConfig(
            agent_id="expert_asking_agent",
            agent_class=ExpertAskingAgent.__name__,
            name=LocaleString(
                en="Expert Asking Agent",
                de="Experten-Abfrage Agent",
                fr="Agent de demande d'expert",
                it="Agente di richiesta esperto",
            ),
            description=LocaleString(
                en="Agent that escalates questions to human experts via Teams or Slack",
                de="Agent, der Fragen an menschliche Experten ueber Teams oder Slack eskaliert",
                fr="Agent qui escalade les questions aux experts humains via Teams ou Slack",
                it="Agente che inoltra le domande agli esperti umani tramite Teams o Slack",
            ),
            llm=LLMConfig(model_name="text-generation/mini"),
            channel_config=get_channel_config(),
        ),
        redis_url=RedisSettings().URL,
        servers=servers_list,
    )

    await runner.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
