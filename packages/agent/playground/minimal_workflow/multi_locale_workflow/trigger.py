from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=True))

import asyncio
import os

from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.core.auth import DangerousDevelopmentOnlyAuthSettings
from swiss_ai_hub.core.events.agent import UserMessageEvent
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.infrastructure import enable_logging

from playground.minimal_workflow.multi_locale_workflow.multi_locale_agent import (
    MultiLocaleAgent,
)
from playground.minimal_workflow.multi_locale_workflow.multi_locale_agent_config import (
    MultiLocaleAgentConfig,
)
from swiss_ai_hub.agent.runners.agent_test_runner import AgentTestRunner

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
