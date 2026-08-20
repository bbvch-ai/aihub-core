"""Manual end-to-end run — GreenMail by default, or a real IMAP account via IMAP_* env vars.

Local GreenMail (default):
    uv run --package swiss-ai-hub-agent python -m app.email_classification_agent.trigger

Real account (e.g. Gmail with an app password):
    IMAP_HOST=imap.gmail.com IMAP_PORT=993 IMAP_TLS=1 \
    IMAP_USER=you@gmail.com IMAP_PASS='app password' \
    IMAP_LLM_MODEL='text-generation/gemma-4-31B-it' \
        uv run --package swiss-ai-hub-agent python -m app.email_classification_agent.trigger

Point it at a mailbox whose category folders do NOT exist yet — the run should create and subscribe them.
"""

import os

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=True))

import asyncio  # noqa: E402

from swiss_ai_hub.core.generative_ai import LLMConfig  # noqa: E402
from swiss_ai_hub.core.i18n import LocaleString  # noqa: E402
from swiss_ai_hub.core.imap import EmailClassificationSettings, ImapClientConfig, MailCategory  # noqa: E402
from swiss_ai_hub.core.infrastructure import enable_logging  # noqa: E402

from swiss_ai_hub.agent.agents.email_classification_agent import (  # noqa: E402
    EmailClassificationAgent,
    EmailClassificationAgentConfig,
)
from swiss_ai_hub.agent.agents.email_classification_agent.events.classify_mail_start_event import (  # noqa: E402
    ClassifyMailStartEvent,
)
from swiss_ai_hub.agent.runners.agent_test_runner import AgentTestRunner  # noqa: E402

enable_logging()

_CATEGORIES = [
    MailCategory(
        category="information_request",
        imap_folder="Triage/Information",
        description="The sender is asking for information we can simply provide — pricing, opening hours, "
        "documentation, where to find something. Answering needs no action beyond telling them.",
    ),
    MailCategory(
        category="support_request",
        imap_folder="Triage/Support",
        description="Something is broken or blocked for the sender and resolving it requires an action from our "
        "team, not just an explanation.",
    ),
    MailCategory(
        category="invoice",
        imap_folder="Triage/Invoices",
        description="A bill, invoice, receipt, payment reminder or dunning notice, whether in the body or attached.",
    ),
]


async def main():
    runner = AgentTestRunner(
        agent_type=EmailClassificationAgent,
        agent_config=EmailClassificationAgentConfig(
            agent_id="email_classification_agent",
            name=LocaleString(en="Email Classification Agent"),
            description=LocaleString(en="Files unread mail into category folders"),
            imap=ImapClientConfig(
                host=os.environ.get("IMAP_HOST", "127.0.0.1"),
                port=int(os.environ.get("IMAP_PORT", "3143")),
                username=os.environ.get("IMAP_USER", "user"),
                password=os.environ.get("IMAP_PASS", "password"),
                use_tls=os.environ.get("IMAP_TLS", "0") == "1",
                inbox_folder=os.environ.get("IMAP_INBOX", "INBOX"),
                enable_move=True,
                processed_folder="",
            ),
            llm=LLMConfig(model_name=os.environ.get("IMAP_LLM_MODEL", "text-generation/gemma-4-31B-it")),
            classification=EmailClassificationSettings(
                categories=_CATEGORIES,
                fallback_folder=os.environ.get("IMAP_FALLBACK", "Triage/Uncategorised"),
            ),
        ),
    )

    async with runner.test_run(delay_before_stop=60) as topic:
        await runner.send_event_from_topic(topic=topic, start_event=ClassifyMailStartEvent())


if __name__ == "__main__":
    asyncio.run(main())
