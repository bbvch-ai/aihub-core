import logging

from swiss_ai_hub.core.auth import UserIdentity
from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import (
    MailClassificationRef,
)
from swiss_ai_hub.core.imap import (
    EmailClassificationSettings,
    ImapClientConfig,
)

from swiss_ai_hub.agent.agents.email_classification_agent.configs.email_classification_agent_config import (
    EmailClassificationAgentConfig,
)
from swiss_ai_hub.agent.agents.email_classification_agent.mail_classifier import (
    CategoryVerdict,
    ClassificationOutcome,
    MailClassifier,
)
from swiss_ai_hub.agent.imap.fetched_mail import FetchedMail
from swiss_ai_hub.agent.imap.step_functions import (
    do_file_messages,
)

logger = logging.getLogger(__name__)


class MailFiler:
    """Classifies a fetched batch with no connection held, then files every message into its folder on one."""

    @staticmethod
    async def classify_all(
        fetched: list[FetchedMail],
        agent_config: EmailClassificationAgentConfig,
        classification: EmailClassificationSettings,
        displayer: EventDisplayer,
        user: UserIdentity | None,
    ) -> list[CategoryVerdict]:
        """Classify every message with no IMAP connection held.

        Inbound mail is untrusted and enters the prompt; the platform's Presidio guard anonymizes PII at the LLM
        gateway, so this step adds no sanitisation of its own.

        Holding the mailbox is the caller's heartbeat, not this loop's business: renewing per message here would
        leave the fetch and the filing either side of it unrenewed, which is how a lease sized for classification
        alone lapses on a slow mailbox.
        """
        llm_config = agent_config.classifier_llm
        verdicts: list[CategoryVerdict] = []
        async with llm_config.cost_reporting_llm(displayer, user=user) as llm:
            for mail in fetched:
                verdict = await MailClassifier.classify(mail.parsed, classification, llm, llm_config.token_counter)
                logger.info(
                    "[classify] uid=%s subject=%r -> %s (%s)",
                    mail.parsed.message_id,
                    mail.parsed.subject,
                    verdict.target_folder(classification),
                    verdict.outcome,
                )
                await MailFiler._report_verdict(mail.parsed.subject, verdict, classification, displayer)
                verdicts.append(verdict)
        return verdicts

    @staticmethod
    async def _report_verdict(
        subject: str,
        verdict: CategoryVerdict,
        classification: EmailClassificationSettings,
        displayer: EventDisplayer,
    ) -> None:
        """Name every failure to whoever is watching the run — a message that quietly moved to a folder nobody looks
        at is the same outage as one that never moved at all."""
        if verdict.outcome is ClassificationOutcome.FAILED:
            await displayer.display_thought(
                f"Could not classify {subject} — filing it in {classification.failure_folder} so it leaves the "
                f"inbox and can be retried by hand."
            )
            return
        await displayer.display_thought(
            f"{subject} → {verdict.category_name or classification.fallback_folder}: {verdict.reason}"
        )

    @staticmethod
    async def file_all(
        fetched: list[FetchedMail],
        verdicts: list[CategoryVerdict],
        imap_config: ImapClientConfig,
        classification: EmailClassificationSettings,
        displayer: EventDisplayer,
    ) -> list[MailClassificationRef]:
        """Move every message into its target folder on one connection, creating the missing folders first.

        The whole batch shares a connection and a single folder check — filing message by message would reconnect
        and re-list the mailbox for each one.

        A failure here aborts the run: messages already filed stay filed, and everything still in the inbox is
        unread, so the next run picks it up. Filing is the only dedup mechanism, so a partial batch is safe. A
        folder the server refuses fails before anything has moved at all.

        A message the classifier could not reach a verdict on is filed too, into `failure_folder`. Leaving it in the
        inbox would have `list_unread` re-select it oldest-first on every run forever; the dedicated folder is what
        makes moving it safe — it keeps its unread flag through the `MOVE`, so an operator dragging it back is the
        retry, and it is never mixed in with mail the model deliberately declined.
        """
        targets = [verdict.target_folder(classification) for verdict in verdicts]
        assignments = [(mail.parsed.message_id, folder) for mail, folder in zip(fetched, targets, strict=True)]
        created = await do_file_messages(imap_config, assignments)

        for folder in sorted(created):
            await displayer.display_thought(f"Created the folder {folder} before filing there.")

        return [
            MailClassificationRef(
                message_id=mail.parsed.message_id,
                sender=mail.parsed.sender,
                subject=mail.parsed.subject,
                category=verdict.category_name,
                target_folder=target_folder,
                reason=verdict.reason,
                folder_created=target_folder in created,
                attachments=mail.attachments,
                original_message=mail.original_message,
            )
            for mail, verdict, target_folder in zip(fetched, verdicts, targets, strict=True)
        ]
