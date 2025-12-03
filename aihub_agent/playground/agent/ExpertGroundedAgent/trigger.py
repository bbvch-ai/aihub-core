import asyncio

from aihub_lib.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthSettings import (
    DangerousDevelopmentOnlyAuthSettings,
)
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.logging.logger import enable_logging
from aihub_lib.nats.events import UserMessageEvent
from llama_index.core.base.llms.types import ChatMessage, MessageRole

from aihub_agent.agents.ExpertGroundedAgent.ExpertGroundedAgent import ExpertGroundedAgent
from aihub_agent.agents.ExpertGroundedAgent.ExpertGroundedAgentConfig import ExpertGroundedAgentConfig
from aihub_agent.runners.AgentTestRunner import AgentTestRunner

enable_logging()


async def main():
    runner = AgentTestRunner(
        agent_type=ExpertGroundedAgent,
        default_agent_config=ExpertGroundedAgentConfig(
            agent_id="grounded_agent",
            agent_class=ExpertGroundedAgent.__name__,
            name=LocaleString(en="Grounded Agent"),
            description=LocaleString(en="This is an agent that can be used to develop the frontend"),
            llm=LLMConfig(model_name="text-generation/mini"),
        ),
    )

    async with runner.test_run(delay_before_stop=70) as topic:
        await runner.send_event_from_topic(
            topic=topic,
            start_event=UserMessageEvent(
                messages=[
                    ChatMessage(
                        content="Philipp Kronenberg started working at bbv 10 years ago "
                        "and went all the way from developer to chief executive operator.",
                        role=MessageRole.SYSTEM,
                    ),
                    ChatMessage(content="Who is the CEO of bbv?", role=MessageRole.USER),
                ],
                user=DangerousDevelopmentOnlyAuthSettings().get_user_identity(),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
