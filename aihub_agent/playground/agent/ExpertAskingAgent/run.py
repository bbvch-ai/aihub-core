# ruff: noqa: E402
from aihub_lib.infrastructure.opentelemetry.AihubInstrumentor import AihubInstrumentor  # isort: skip
from aihub_lib.nats.events.bot_in_the_loop.request.BotInTheLoopRequestEvent import TeamsConfig

AihubInstrumentor().instrument()

import asyncio

from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.logging.logger import enable_logging

from aihub_agent.agents.ExpertAskingAgent.ExpertAskingAgent import ExpertAskingAgent
from aihub_agent.agents.ExpertAskingAgent.ExpertAskingAgentConfig import ExpertAskingAgentConfig
from aihub_agent.runners.AgentTestRunner import AgentTestRunner

enable_logging()


async def main():
    runner = AgentTestRunner(
        agent_type=ExpertAskingAgent,
        default_agent_config=ExpertAskingAgentConfig(
            agent_id="expert_agent",
            agent_class=ExpertAskingAgent.__name__,
            name=LocaleString(en="Expert Asking Agent"),
            description=LocaleString(en="This is an agent that can be used to develop the frontend"),
            llm=LLMConfig(model_name="text-generation/mini"),
            # channel_config=SlackConfig(
            #     channel_id="C08MK7Z8GU9",
            # ),
            channel_config=TeamsConfig(
                channel_id="19:zAzZDk2wJBx_2WR949Eh25xG-UntOkk1BtykJ27Qcrk1@thread.tacv2",
                tenant_id="37314c94-c755-48ab-85bb-acb83e492c42",
                bot_id="ac98b506-ec21-46b9-a31e-80d34c6eb71e",
            ),
        ),
    )

    await runner.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
