from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=True))

import asyncio

from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.core.auth import DangerousDevelopmentOnlyAuthSettings
from swiss_ai_hub.core.events.agent import UserMessageEvent
from swiss_ai_hub.core.i18n import LocaleString

from playground.minimal_workflow.configured_workflow.configured_agent import (
    ConfiguredAgent,
)
from playground.minimal_workflow.configured_workflow.configured_agent_config import (
    ConfiguredAgentConfig,
    StartStepConfig,
)
from swiss_ai_hub.agent.runners.agent_test_runner import AgentTestRunner


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
