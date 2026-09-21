"""Manual end-to-end run — GreenMail by default, or a real IMAP account via IMAP_* env vars.

Local GreenMail (default, runs the read/move chain):
    uv run --package swiss-ai-hub-agent python -m app.imap_agent.trigger

Run the independent drafting chain instead (reads from IMAP_DRAFT_SOURCE, default INBOX):
    IMAP_TRIGGER=draft IMAP_DRAFT_SOURCE=Processed \
        uv run --package swiss-ai-hub-agent python -m app.imap_agent.trigger

Real account (e.g. Gmail with an app password):
    IMAP_HOST=imap.gmail.com IMAP_PORT=993 IMAP_TLS=1 \
    IMAP_USER=you@gmail.com IMAP_PASS='app password' \
    IMAP_DRAFTS='[Gmail]/Drafts' IMAP_PROCESSED='Processed' IMAP_ENABLE_MOVE=1 IMAP_ENABLE_DRAFT=1 \
        uv run --package swiss-ai-hub-agent python -m app.imap_agent.trigger
"""

import os

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=True))

import asyncio  # noqa: E402

from swiss_ai_hub.core.i18n import LocaleString  # noqa: E402
from swiss_ai_hub.core.imap import DraftEmailSettings, ImapClientConfig  # noqa: E402
from swiss_ai_hub.core.infrastructure import enable_logging  # noqa: E402

from swiss_ai_hub.agent.agents.imap_agent import ImapAgent, ImapAgentConfig  # noqa: E402
from swiss_ai_hub.agent.agents.imap_agent.events.draft_mail_start_event import DraftMailStartEvent  # noqa: E402
from swiss_ai_hub.agent.agents.imap_agent.events.read_mail_start_event import ReadMailStartEvent  # noqa: E402
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
                host=os.environ.get("IMAP_HOST", "127.0.0.1"),
                port=int(os.environ.get("IMAP_PORT", "3143")),
                username=os.environ.get("IMAP_USER", "user"),
                password=os.environ.get("IMAP_PASS", "password"),
                use_tls=os.environ.get("IMAP_TLS", "0") == "1",
                inbox_folder=os.environ.get("IMAP_INBOX", "INBOX"),
                enable_move=os.environ.get("IMAP_ENABLE_MOVE", "1") == "1",
                processed_folder=os.environ.get("IMAP_PROCESSED", "Processed"),
            ),
            draft=DraftEmailSettings(
                enable_draft=os.environ.get("IMAP_ENABLE_DRAFT", "1") == "1",
                source_folder=os.environ.get("IMAP_DRAFT_SOURCE", "INBOX"),
                batch_size=int(os.environ.get("IMAP_DRAFT_BATCH", "5")),
                drafts_folder=os.environ.get("IMAP_DRAFTS", "Drafts"),
                model_name=os.environ.get("IMAP_LLM_MODEL", "text-generation/gemma-4-31B-it"),
            ),
        ),
    )

    start_event = DraftMailStartEvent() if os.environ.get("IMAP_TRIGGER", "read") == "draft" else ReadMailStartEvent()
    async with runner.test_run(delay_before_stop=30) as topic:
        await runner.send_event_from_topic(topic=topic, start_event=start_event)


if __name__ == "__main__":
    asyncio.run(main())
