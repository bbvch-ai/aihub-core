# ruff: noqa: E402
from aihub_lib.infrastructure.opentelemetry.AihubInstrumentor import AihubInstrumentor  # isort: skip
from dotenv import load_dotenv

AihubInstrumentor().instrument()

import asyncio
import os

from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.logging.logger import enable_logging
from aihub_lib.nats.events.bot_in_the_loop.request.BotInTheLoopRequestEvent import SlackConfig, TeamsConfig

from aihub_agent.agents.ExpertAskingAgent.ExpertAskingAgent import ExpertAskingAgent
from aihub_agent.agents.ExpertAskingAgent.ExpertAskingAgentConfig import ExpertAskingAgentConfig
from aihub_agent.runners.AgentTestRunner import AgentTestRunner

enable_logging()
load_dotenv()


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
    runner = AgentTestRunner(
        agent_type=ExpertAskingAgent,
        default_agent_config=ExpertAskingAgentConfig(
            agent_id="expert_agent",
            agent_class=ExpertAskingAgent.__name__,
            name=LocaleString(en="Expert Asking Agent"),
            description=LocaleString(en="This is an agent that can be used to develop the frontend"),
            llm=LLMConfig(model_name="text-generation/mini"),
            channel_config=get_channel_config(),
        ),
    )

    await runner.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
