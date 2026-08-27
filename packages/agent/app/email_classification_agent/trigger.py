"""Manual end-to-end run — GreenMail by default, or a real IMAP account via IMAP_* env vars.

Local GreenMail (default):
    uv run --package swiss-ai-hub-agent python -m app.email_classification_agent.trigger

Real account (e.g. Gmail with an app password):
    IMAP_HOST=imap.gmail.com IMAP_PORT=993 IMAP_TLS=1 \
    IMAP_USER=you@gmail.com IMAP_PASS='app password' \
    IMAP_LLM_MODEL='text-generation/gemma-4-31B-it' \
        uv run --package swiss-ai-hub-agent python -m app.email_classification_agent.trigger

Scheduled entry point (same run, fired the way the cron scheduler fires it):
    SCHEDULED=1 uv run --package swiss-ai-hub-agent python -m app.email_classification_agent.trigger

Point it at a mailbox whose category folders do NOT exist yet — the run should create and subscribe them.

Running two of these at once against the same mailbox is the overlap check: exactly one should classify and file,
the other should report that a previous run still holds the mailbox and stop.

Drafting is on by default here (the shipped template has it off). Two of the three categories ask for a reply, so a
run over mixed mail should leave drafts for the information and support mail and none for the invoice. Add
`IMAP_INCLUDE_ATTACHMENTS=1` to also feed attachment text to the drafter — that needs MinerU reachable for PDFs and
images; Word and other Office files go through MarkItDown in-process.

Nothing is ever sent. Check the Sent folder afterwards: it must be untouched.
"""

import os

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=True))

import asyncio  # noqa: E402
from datetime import UTC, datetime  # noqa: E402

from swiss_ai_hub.core.events.agent import CronStartEvent  # noqa: E402
from swiss_ai_hub.core.generative_ai import LLMConfig  # noqa: E402
from swiss_ai_hub.core.i18n import LocaleString  # noqa: E402
from swiss_ai_hub.core.imap import (  # noqa: E402
    DraftEmailSettings,
    EmailClassificationSettings,
    ImapClientConfig,
    MailCategory,
)
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
        draft_reply=True,
    ),
    MailCategory(
        category="support_request",
        imap_folder="Triage/Support",
        description="Something is broken or blocked for the sender and resolving it requires an action from our "
        "team, not just an explanation.",
        draft_reply=True,
    ),
    MailCategory(
        category="invoice",
        imap_folder="Triage/Invoices",
        description="A bill, invoice, receipt, payment reminder or dunning notice, whether in the body or attached.",
        # Deliberately off, so one run shows both answers: two categories drafted, one not.
        draft_reply=False,
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
            draft=DraftEmailSettings(
                enable_draft=os.environ.get("IMAP_ENABLE_DRAFT", "1") == "1",
                drafts_folder=os.environ.get("IMAP_DRAFTS", "Drafts"),
                model_name=os.environ.get("IMAP_LLM_MODEL", "text-generation/gemma-4-31B-it"),
                include_attachments=os.environ.get("IMAP_INCLUDE_ATTACHMENTS", "0") == "1",
            ),
        ),
    )

    # Both entry points run the identical workflow; SCHEDULED=1 is what proves the union on the entry step is
    # wired, without waiting on a cron occurrence.
    start_event = (
        CronStartEvent(scheduled_for=datetime.now(UTC))
        if os.environ.get("SCHEDULED") == "1"
        else ClassifyMailStartEvent()
    )
    # A full batch is one model call per message to classify, then another per drafted message, plus a document-parser
    # round trip per attachment when IMAP_INCLUDE_ATTACHMENTS is on. Sixty seconds was enough when the run only
    # classified; it now cuts the run off mid-batch, which leaves the mailbox leased until the TTL expires. Raise
    # IMAP_RUN_SECONDS further for a large mailbox or a slow model.
    async with runner.test_run(delay_before_stop=int(os.environ.get("IMAP_RUN_SECONDS", "600"))) as topic:
        await runner.send_event_from_topic(topic=topic, start_event=start_event)


if __name__ == "__main__":
    asyncio.run(main())
