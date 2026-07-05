"""Manual end-to-end run against a local plaintext IMAP test server (e.g. GreenMail on port 3143)."""

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=True))

import asyncio  # noqa: E402

from llama_index.core.base.llms.types import ChatMessage, MessageRole  # noqa: E402
from swiss_ai_hub.core.events.agent import UserMessageEvent  # noqa: E402
from swiss_ai_hub.core.i18n import LocaleString  # noqa: E402
from swiss_ai_hub.core.imap import ImapClientConfig  # noqa: E402
from swiss_ai_hub.core.infrastructure import enable_logging  # noqa: E402
from swiss_ai_hub.core.testing.auth_utils import fake_user  # noqa: E402

from playground.minimal_workflow.imap_workflow.imap_agent import ImapAgent  # noqa: E402
from playground.minimal_workflow.imap_workflow.imap_agent_config import ImapAgentConfig  # noqa: E402
from swiss_ai_hub.agent.runners.agent_test_runner import AgentTestRunner  # noqa: E402

enable_logging()


async def main():
    runner = AgentTestRunner(
        agent_type=ImapAgent,
        agent_config=ImapAgentConfig(
            agent_id="imap_agent",
            name=LocaleString(en="IMAP Agent"),
            description=LocaleString(en="Reads unread mail from an IMAP inbox"),
            imap=ImapClientConfig(
                host="127.0.0.1",
                port=3143,
                username="user",
                password="password",
                use_tls=False,
            ),
        ),
    )

    async with runner.test_run(delay_before_stop=30) as topic:
        await runner.send_event_from_topic(
            topic=topic,
            start_event=UserMessageEvent(
                messages=[ChatMessage(content="Read my unread mail", role=MessageRole.USER)],
                user=fake_user(),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
