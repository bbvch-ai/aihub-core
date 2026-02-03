import asyncio
import os

from aihub_lib.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthSettings import (
    DangerousDevelopmentOnlyAuthSettings,
)
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.logging.logger import enable_logging
from aihub_lib.nats.events import UserMessageEvent
from llama_index.core.base.llms.types import ChatMessage, MessageRole

from aihub_agent.runners.AgentTestRunner import AgentTestRunner
from playground.minimal_workflow.multi_locale_workflow.MultiLocaleAgent import (
    MultiLocaleAgent,
)
from playground.minimal_workflow.multi_locale_workflow.MultiLocaleAgentConfig import (
    MultiLocaleAgentConfig,
)

enable_logging()


async def main():
    runner = AgentTestRunner(
        agent_type=MultiLocaleAgent,
        agent_config=MultiLocaleAgentConfig(
            agent_id="multi_locale_agent",
            agent_class=MultiLocaleAgent.__name__,
            name=LocaleString(en="Multi Locale Agent"),
            description=LocaleString(en="This is an agent that knows multiple languages"),
            locale_path="myagent.myscope.test",
        ),
        locale_paths=[os.path.join(os.path.dirname(os.path.abspath(__file__)), "translations")],
    )

    async with runner.test_run(delay_before_stop=1) as topic:
        await runner.send_event_from_topic(
            start_event=UserMessageEvent(
                locale="en",
                messages=[ChatMessage(content="Hello", role=MessageRole.USER)],
                user=DangerousDevelopmentOnlyAuthSettings().get_user_identity(),
            ),
            topic=topic,
        )


if __name__ == "__main__":
    asyncio.run(main())
