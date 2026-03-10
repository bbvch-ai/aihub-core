import asyncio

from swiss_ai_hub.core.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthSettings import (
    DangerousDevelopmentOnlyAuthSettings,
)
from swiss_ai_hub.core.generative_ai.resources.models.llm.LLMConfig import LLMConfig, LLMParameter
from swiss_ai_hub.core.i18n.LocaleString import LocaleString
from swiss_ai_hub.core.nats.events.user.UserMessageEvent import UserMessageEvent

from playground.minimal_workflow.user_memory_workflow.UserMemoryAgent import UserMemoryAgent
from playground.minimal_workflow.user_memory_workflow.UserMemoryAgentConfig import UserMemoryAgentConfig
from swiss_ai_hub.agent.runners.AgentTestRunner import AgentTestRunner


async def main():
    """One-shot test runner for UserMemoryAgent."""
    runner = AgentTestRunner(
        agent_type=UserMemoryAgent,
        agent_config=UserMemoryAgentConfig(
            agent_class=UserMemoryAgent.__name__,
            agent_id="memory_agent",
            name=LocaleString(en="User Memory Agent"),
            description=LocaleString(en="This is the Memory Agent config"),
            llm=LLMConfig(
                model_name="text-generation/gpt-oss-120b",
                default_parameter=LLMParameter(temperature=1.0),
            ),
        ),
    )
    async with runner.test_run() as topic:
        await runner.send_event_from_topic(
            topic=topic,
            start_event=UserMessageEvent(
                messages=[],
                user=DangerousDevelopmentOnlyAuthSettings().get_user_identity(),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
