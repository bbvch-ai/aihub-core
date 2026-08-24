import logging
from collections import Counter
from typing import ClassVar

from swiss_ai_hub.core.auth import UserIdentity
from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import (
    MailBatchClassifiedEvent,
    MailClassificationRef,
    StopEvent,
    UnreadMailListedEvent,
)
from swiss_ai_hub.core.imap import EmailClassificationSettings, ImapClientConfig
from swiss_ai_hub.core.topics import AgentInstanceTopic

from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.agents.email_classification_agent.configs.email_classification_agent_config import (
    EmailClassificationAgentConfig,
)
from swiss_ai_hub.agent.agents.email_classification_agent.events.classify_mail_start_event import (
    ClassifyMailStartEvent,
)
from swiss_ai_hub.agent.agents.email_classification_agent.mail_classifier import CategoryVerdict, MailClassifier
from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString
from swiss_ai_hub.agent.imap.fetched_mail import FetchedMail
from swiss_ai_hub.agent.imap.step_functions import do_fetch_and_archive, do_file_messages, do_list_unread
from swiss_ai_hub.agent.workflow.decorators.step import step

logger = logging.getLogger(__name__)


class EmailClassificationAgent(Agent):
    """Files every unread message in a mailbox into the folder for its category.

    Non-conversational, like RetrievalAgent: triggered programmatically, configured via its form, not exposed in the
    chat UI. Categories are configuration — a name, a target folder, and a description of what belongs in it — so a
    customer adds or renames one without a deployment.

    Mail the model is not confident about is never forced into a bucket; it goes to the configured fallback folder.
    Filing is also what makes a re-run safe: every message leaves the inbox, so the next unread listing cannot see it.

    The agent reads and files. It never sends — there is no SMTP path anywhere in the platform.
    """

    name: ClassVar[AgentLocaleString] = AgentLocaleString.from_i18n_path(
        "agent.email_classification_agent.metadata.name"
    )
    description: ClassVar[AgentLocaleString] = AgentLocaleString.from_i18n_path(
        "agent.email_classification_agent.metadata.description"
    )
    icon: ClassVar[str] = "mage:folder-check"

    @step(
        name=AgentLocaleString.from_i18n_path("agent.email_classification_agent.steps.list_unread.name"),
        icon="mage:inbox",
    )
    async def list_unread_step(
        self,
        _event: ClassifyMailStartEvent,
        imap_config: ImapClientConfig,
    ) -> UnreadMailListedEvent:
        """List every unread message in the inbox, oldest sent first, capped by max_messages."""
        return UnreadMailListedEvent(messages=await do_list_unread(imap_config))

    @step(
        name=AgentLocaleString.from_i18n_path("agent.email_classification_agent.steps.classify_and_file.name"),
        icon="mage:folder-check",
    )
    async def classify_and_file_step(
        self,
        event: UnreadMailListedEvent,
        agent_config: EmailClassificationAgentConfig,
        imap_config: ImapClientConfig,
        classification: EmailClassificationSettings,
        topic: AgentInstanceTopic,
        displayer: EventDisplayer,
        # Optional, unlike the conversational agents: this agent is triggered programmatically and its
        # start events default user to None, so a scheduler-driven run has no identity to attribute.
        user: UserIdentity | None = None,
    ) -> MailBatchClassifiedEvent:
        """Classify the whole unread batch and file each message into the folder for its category.

        One looping step rather than event fan-out: the engine's fixed-size join needs a compile-time constant and
        the message count is only known at runtime — the same reason the drafting chain loops.

        Three phases, and the split between them is deliberate. The IMAP connection is opened for the fetch, closed
        for the model calls, and reopened to file: many servers drop a socket left idle across a slow batch of LLM
        round-trips.

        The batch can come back shorter than the listing: this is a shared mailbox, so a human may file or delete a
        message by hand between the two, and one that vanished is skipped rather than failing the run.
        """
        self._validate(classification, imap_config.inbox_folder)

        if not event.messages:
            logger.info("[classify] inbox has no unread mail — nothing to classify")
            await displayer.display_thought("No unread messages in the inbox.")
            return MailBatchClassifiedEvent(source_folder=imap_config.inbox_folder, count=0)

        fetched = await do_fetch_and_archive(
            imap_config,
            [message.message_id for message in event.messages],
            agent_class=topic.agent_class,
            agent_id=topic.agent_id,
            skip_vanished=True,
        )
        verdicts = await self._classify_all(fetched, agent_config, classification, displayer, user)
        classified = await self._file_all(fetched, verdicts, imap_config, classification, displayer)

        per_category = Counter(ref.category for ref in classified if ref.category)
        fallback_count = sum(1 for ref in classified if ref.category is None)
        logger.info(
            "[classify] filed %d message(s): %s, fallback=%d", len(classified), dict(per_category), fallback_count
        )
        return MailBatchClassifiedEvent(
            source_folder=imap_config.inbox_folder,
            count=len(classified),
            per_category=dict(per_category),
            fallback_count=fallback_count,
            classified=classified,
        )

    @step(
        name=AgentLocaleString.from_i18n_path("agent.email_classification_agent.steps.finish.name"),
        icon="mage:check",
    )
    async def finish_classification_step(self, event: MailBatchClassifiedEvent) -> StopEvent:
        """Terminate the run once the batch has been filed."""
        logger.info("[classify] run complete — %d message(s) filed", event.count)
        return StopEvent()

    @staticmethod
    def _validate(classification: EmailClassificationSettings, inbox_folder: str) -> None:
        """Fail the run rather than silently filing everything into the fallback folder."""
        if not classification.categories:
            raise ValueError("no categories are configured — the agent has nothing to classify into")
        if not classification.fallback_folder:
            raise ValueError("fallback_folder is empty — mail the model is unsure about would have nowhere to go")

        names = [category.category for category in classification.categories]
        folders = [category.imap_folder for category in classification.categories]
        if len(set(names)) != len(names):
            raise ValueError(f"category names must be unique, got {names}")
        if len(set(folders)) != len(folders):
            raise ValueError(f"category folders must be unique, got {folders}")
        if classification.fallback_folder in folders:
            raise ValueError(
                f"fallback_folder {classification.fallback_folder!r} is also a category folder — the run summary "
                "could not tell a categorised message from an uncategorised one"
            )

        # Filing out of the inbox is the only dedup this agent has, and a target equal to the inbox defeats it.
        # On the COPY + UID EXPUNGE path the original is replaced by a fresh unread copy in the same folder, so the
        # next run classifies the copy, archives it again, and repeats without termination. Folder names are
        # admin-entered free text, so this is reachable by a typo rather than only by misuse.
        if inbox_folder in {*folders, classification.fallback_folder}:
            raise ValueError(
                f"a target folder equals the inbox folder {inbox_folder!r} — filed mail would stay unread in the "
                "inbox and be reprocessed on every run"
            )

    async def _classify_all(
        self,
        fetched: list[FetchedMail],
        agent_config: EmailClassificationAgentConfig,
        classification: EmailClassificationSettings,
        displayer: EventDisplayer,
        user: UserIdentity | None,
    ) -> list[CategoryVerdict]:
        """Classify every message with no IMAP connection held.

        Inbound mail is untrusted and enters the prompt; the platform's Presidio guard anonymizes PII at the LLM
        gateway, so this step adds no sanitisation of its own.
        """
        llm_config = agent_config.classifier_llm
        verdicts: list[CategoryVerdict] = []
        async with llm_config.cost_reporting_llm(displayer, user=user) as llm:
            for mail in fetched:
                verdict = await MailClassifier.classify(mail.parsed, classification, llm)
                logger.info(
                    "[classify] uid=%s subject=%r -> %s",
                    mail.parsed.message_id,
                    mail.parsed.subject,
                    verdict.category_name or "<fallback>",
                )
                await displayer.display_thought(
                    f"{mail.parsed.subject} → {verdict.category_name or classification.fallback_folder}: "
                    f"{verdict.reason}"
                )
                verdicts.append(verdict)
        return verdicts

    async def _file_all(
        self,
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
        """
        targets = [
            verdict.category.imap_folder if verdict.category else classification.fallback_folder for verdict in verdicts
        ]
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
