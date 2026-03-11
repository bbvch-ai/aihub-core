import asyncio

from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.core.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthSettings import (
    DangerousDevelopmentOnlyAuthSettings,
)
from swiss_ai_hub.core.events.agent.user.UserMessageEvent import UserMessageEvent
from swiss_ai_hub.core.i18n.LocaleString import LocaleString

from playground.minimal_workflow.configured_workflow.ConfiguredAgent import (
    ConfiguredAgent,
)
from playground.minimal_workflow.configured_workflow.ConfiguredAgentConfig import (
    ConfiguredAgentConfig,
    StartStepConfig,
)
from swiss_ai_hub.agent.runners.AgentTestRunner import AgentTestRunner


async def main():
    runner = AgentTestRunner(
        agent_type=ConfiguredAgent,
        agent_config=ConfiguredAgentConfig(
            agent_id="configured_agent",
            name=LocaleString(en="Configured Agent"),
            description=LocaleString(en="This is a configured agent"),
            some_agent_value="Value on agent config",
            start_step_config=StartStepConfig(some_step_value="Value on step config"),
        ),
    )
    async with runner.test_run() as topic:
        await runner.send_event_from_topic(
            topic=topic,
            start_event=UserMessageEvent(
                messages=[ChatMessage(content="Hello", role=MessageRole.USER)],
                user=DangerousDevelopmentOnlyAuthSettings().get_user_identity(),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
