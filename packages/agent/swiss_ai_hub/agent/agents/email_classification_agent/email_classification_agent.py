import email
import logging
from collections import Counter
from email.policy import default as default_policy
from typing import ClassVar

from llama_index.core.base.llms.types import ChatMessage, MessageRole
from redis.asyncio import Redis
from swiss_ai_hub.core.auth import UserIdentity
from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import (
    CronStartEvent,
    MailBatchClassifiedEvent,
    MailBatchDraftedEvent,
    MailClassificationRef,
    StopEvent,
    UnreadMailListedEvent,
)
from swiss_ai_hub.core.imap import DraftEmailSettings, EmailClassificationSettings, ImapClientConfig
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
from swiss_ai_hub.agent.imap.attachment_text_extractor import AttachmentTextExtractor
from swiss_ai_hub.agent.imap.composed_reply import ComposedReply
from swiss_ai_hub.agent.imap.draft_prompt_builder import DraftPromptBuilder
from swiss_ai_hub.agent.imap.extracted_attachment import AttachmentOutcome, ExtractedAttachment
from swiss_ai_hub.agent.imap.fetched_mail import FetchedMail
from swiss_ai_hub.agent.imap.mail_parser import MailParser
from swiss_ai_hub.agent.imap.mail_store import MailStore
from swiss_ai_hub.agent.imap.mailbox_lease_lost_error import MailboxLeaseLostError
from swiss_ai_hub.agent.imap.mailbox_run_lease import MailboxRunLease
from swiss_ai_hub.agent.imap.parsed_message import ParsedMessage
from swiss_ai_hub.agent.imap.reply_composer import ReplyComposer
from swiss_ai_hub.agent.imap.step_functions import (
    do_draft_replies,
    do_fetch_and_archive,
    do_file_messages,
    do_list_unread,
)
from swiss_ai_hub.agent.workflow.decorators.step import step

logger = logging.getLogger(__name__)


class EmailClassificationAgent(Agent):
    """Files every unread message in a mailbox into the folder for its category, and drafts replies to the ones the
    admin asked for.

    Non-conversational, like RetrievalAgent: triggered programmatically, configured via its form, not exposed in the
    chat UI. Categories are configuration — a name, a target folder, and a description of what belongs in it — so a
    customer adds or renames one without a deployment.

    Schedulable: accepting `CronStartEvent` alongside its own start event is the entire opt-in, and the platform-owned
    `cron` field on the `AgentConfig` base is what `CronScheduler` reads to decide when a profile fires. Scheduled runs
    carry no user, which costs this agent nothing — it reads its mailbox and its tenant from its own profile.

    Mail the model is not confident about is never forced into a bucket; it goes to the configured fallback folder.
    Filing is also what makes a re-run safe: every message leaves the inbox, so the next unread listing cannot see it.
    Filing is only the dedup *between* runs, though: a message is unread right up until it moves, so two runs
    overlapping on a slow mailbox would both classify and file the same batch. `MailboxRunLease` is what stops that,
    and unattended scheduling is exactly what makes the overlap reachable.

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
        _event: ClassifyMailStartEvent | CronStartEvent,
        imap_config: ImapClientConfig,
        topic: AgentInstanceTopic,
        redis: Redis,
        displayer: EventDisplayer,
    ) -> UnreadMailListedEvent | StopEvent:
        """Claim the mailbox, then list every unread message in it, oldest sent first, capped by max_messages.

        Accepting `CronStartEvent` here is what makes the blueprint schedulable — `AgentRunner` derives
        `is_schedulable` from the declared start events, so there is nothing else to register.

        Claiming before listing is the point: everything after this is slow (a fetch, one LLM call per message, then
        the filing), and the messages stay unread throughout, so a second run entering here would redo all of it. A run
        that cannot claim stops rather than queueing — the holder is already filing the mail this run would have found.
        """
        if not await MailboxRunLease(redis).acquire(topic.agent_class, topic.agent_id, topic.run_id):
            await displayer.display_thought(
                "A previous run is still filing this mailbox — skipping this one rather than classifying its "
                "mail twice."
            )
            return StopEvent()

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
        draft: DraftEmailSettings,
        topic: AgentInstanceTopic,
        displayer: EventDisplayer,
        redis: Redis,
        # Optional, unlike the conversational agents: this agent is triggered programmatically and its
        # start events default user to None, so a cron-driven run has no identity to attribute.
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

        All three phases run under one heartbeat rather than renewing the lease at points along the way: the fetch and
        the filing pass are as capable of outliving the TTL as the model calls are, and neither offers a per-item hook
        to renew from.
        """
        self._validate(classification, draft, imap_config.inbox_folder)
        lease = MailboxRunLease(redis)

        if not event.messages:
            logger.info("[classify] inbox has no unread mail — nothing to classify")
            await displayer.display_thought("No unread messages in the inbox.")
            return MailBatchClassifiedEvent(source_folder=imap_config.inbox_folder, count=0)

        async with lease.heartbeat(topic.agent_class, topic.agent_id, topic.run_id):
            fetched = await do_fetch_and_archive(
                imap_config,
                [message.message_id for message in event.messages],
                agent_class=topic.agent_class,
                agent_id=topic.agent_id,
                skip_vanished=True,
            )
            verdicts = await self._classify_all(fetched, agent_config, classification, displayer, user)

            # Checked here and not earlier because filing is the only phase that mutates the mailbox: a fetch or a
            # classification this run no longer owns has wasted time and money, but only filing can put two runs on
            # the same messages.
            if lease.lost:
                raise MailboxLeaseLostError(
                    f"run {topic.run_id} lost the mailbox lease on {topic.agent_class}/{topic.agent_id} before "
                    f"filing {len(fetched)} message(s) — another run holds it, so this run files nothing"
                )

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
        name=AgentLocaleString.from_i18n_path("agent.email_classification_agent.steps.draft_replies.name"),
        icon="mage:pen",
    )
    async def draft_replies_step(
        self,
        event: MailBatchClassifiedEvent,
        agent_config: EmailClassificationAgentConfig,
        imap_config: ImapClientConfig,
        classification: EmailClassificationSettings,
        draft: DraftEmailSettings,
        topic: AgentInstanceTopic,
        displayer: EventDisplayer,
        redis: Redis,
    ) -> MailBatchDraftedEvent | StopEvent:
        """Draft a reply for each filed message whose category was opted into drafting, and leave it in Drafts.

        This is the terminal step whenever there is nothing to draft, which is why it releases the lease itself — the
        release travels with whichever step ends the run, not with a method named `finish`.

        Drafting reads each message back from the S3 archive rather than from IMAP or from the event. The UID died
        with the `MOVE` that filed it, and a body of up to `max_body_bytes` per message has no business on an event
        that is persisted to the audit trail and streamed to the frontend. The archived `.eml` is the message
        verbatim, so it is also the better input: recipients and the full body survive the round trip.

        Nothing is flagged as drafted. Filing already prevents a second run seeing this mail, so the flag #1509 needs
        for its own unread-source chain would be writing to a UID that no longer resolves.

        The agent still never sends. A draft is an IMAP `APPEND`; there is no SMTP path anywhere in the platform.
        """
        lease = MailboxRunLease(redis)
        to_draft = self._drafting_batch(event, classification, draft)
        if not to_draft:
            await self._report_nothing_to_draft(event, classification, draft, displayer)
            await lease.release(topic.agent_class, topic.agent_id, topic.run_id)
            return StopEvent()

        async with lease.heartbeat(topic.agent_class, topic.agent_id, topic.run_id):
            replies = await self._compose_all(to_draft, agent_config, draft, imap_config, topic, displayer)

            # Checked before the first APPEND for the same reason filing is: up to here a lost lease has only cost
            # time and model spend, while appending puts a second run's drafts in the same folder.
            if lease.lost:
                raise MailboxLeaseLostError(
                    f"run {topic.run_id} lost the mailbox lease on {topic.agent_class}/{topic.agent_id} before "
                    f"appending {len(replies)} draft(s) — another run holds it, so this run drafts nothing"
                )

            drafted = await do_draft_replies(imap_config, draft.drafts_folder, replies)

        per_category = Counter(ref.category for ref in drafted if ref.category)
        # The folder the server actually accepted, which is not always the configured name — Gmail resolves a
        # mistyped or localized name to its own `[Gmail]/Drafts`, and telling the admin the wrong folder to look in
        # is how a working run gets reported as a broken one.
        landed_in = drafted[0].drafts_folder if drafted else draft.drafts_folder
        logger.info("[draft] appended %d draft(s) to %r: %s", len(drafted), landed_in, dict(per_category))
        await displayer.display_thought(
            f"Left {len(drafted)} reply draft(s) in {landed_in} for review. Nothing was sent."
        )
        return MailBatchDraftedEvent(
            source_folder=imap_config.inbox_folder,
            count=len(drafted),
            per_category=dict(per_category),
            skipped_count=event.count - len(to_draft),
            drafted=drafted,
        )

    @step(
        name=AgentLocaleString.from_i18n_path("agent.email_classification_agent.steps.finish.name"),
        icon="mage:check",
    )
    async def finish_drafting_step(
        self,
        event: MailBatchDraftedEvent,
        topic: AgentInstanceTopic,
        redis: Redis,
    ) -> StopEvent:
        """Release the mailbox and terminate the run once the drafts have been appended.

        The release belongs in whichever step returns the terminal `StopEvent`, not in this method by name — a later
        story that appends work after drafting has to move it with the terminal step, or the mailbox stays claimed
        until the lease expires and the next occurrence is skipped for no reason.
        `test_every_terminal_step_accounts_for_the_lease` is what enforces that, across both terminal steps.

        A run that raises never reaches here: the dispatcher tears down on `ExceptionEvent` before any step could run,
        so the lease TTL is the sole recovery path for a failed run.
        """
        await MailboxRunLease(redis).release(topic.agent_class, topic.agent_id, topic.run_id)
        logger.info("[draft] run complete — %d draft(s) appended", event.count)
        return StopEvent()

    @staticmethod
    def _drafting_batch(
        event: MailBatchClassifiedEvent,
        classification: EmailClassificationSettings,
        draft: DraftEmailSettings,
    ) -> list[MailClassificationRef]:
        """The filed messages that are due a draft: those whose category the admin opted in.

        Mail that went to the fallback folder has no category and so can never be opted in — which is the intended
        behaviour, not an oversight. A model that could not place a message is in no position to answer it.

        A message missing its archive reference is dropped here rather than failing the run: its mail is already
        filed, and one unarchivable message must not cost the whole batch its drafts.
        """
        if not draft.enable_draft:
            return []

        opted_in = {category.category for category in classification.categories if category.draft_reply}
        return [
            ref for ref in event.classified if ref.category in opted_in and EmailClassificationAgent._is_archived(ref)
        ]

    @staticmethod
    def _is_archived(ref: MailClassificationRef) -> bool:
        if ref.original_message:
            return True
        logger.warning("[draft] uid=%s has no archived original — cannot draft a reply to it, skipping", ref.message_id)
        return False

    @staticmethod
    async def _report_nothing_to_draft(
        event: MailBatchClassifiedEvent,
        classification: EmailClassificationSettings,
        draft: DraftEmailSettings,
        displayer: EventDisplayer,
    ) -> None:
        """Say why no draft was written, so a silent run is never ambiguous between 'off' and 'nothing matched'."""
        if not draft.enable_draft:
            logger.info("[draft] enable_draft=False — filed %d message(s), drafting none", event.count)
            await displayer.display_thought("Reply drafting is disabled — no drafts were written.")
            return

        opted_in = sorted(category.category for category in classification.categories if category.draft_reply)
        logger.info("[draft] no message in this batch belongs to a drafting category %s", opted_in)
        await displayer.display_thought(
            f"No mail in this run belongs to a category that gets a drafted reply ({', '.join(opted_in)})."
            if opted_in
            else "No category is set to get a drafted reply — no drafts were written."
        )

    async def _compose_all(
        self,
        to_draft: list[MailClassificationRef],
        agent_config: EmailClassificationAgentConfig,
        draft: DraftEmailSettings,
        imap_config: ImapClientConfig,
        topic: AgentInstanceTopic,
        displayer: EventDisplayer,
    ) -> list[tuple[MailClassificationRef, ComposedReply]]:
        """Draft every reply body with no IMAP connection held, then pair each with its threaded envelope.

        The connection is deliberately absent for the whole of this: one model call per message over a batch is
        exactly the stretch of time a mail server drops an idle socket in.

        Inbound mail is untrusted and enters the prompt; the platform's Presidio guard anonymizes PII at the LLM
        gateway, so this adds no sanitisation of its own.
        """
        llm_config = agent_config.drafting_llm
        builder = DraftPromptBuilder(draft.number_of_input_tokens, llm_config.token_counter, draft.draft_prompt)
        replies: list[tuple[MailClassificationRef, ComposedReply]] = []

        async with llm_config.cost_reporting_llm(displayer) as llm:
            for classification_ref in to_draft:
                parsed = await self._reparse_archived(classification_ref, imap_config, topic)
                attachments = await self._extracted_attachments(classification_ref, draft, topic, displayer)
                await displayer.display_thought(f"Drafting a reply to: {parsed.subject}")
                messages = [
                    ChatMessage(role=MessageRole.SYSTEM, content=draft.draft_prompt),
                    ChatMessage(role=MessageRole.USER, content=builder.build(parsed, attachments)),
                ]
                llm_event = await displayer.display_llm_stream(llm_config, llm, messages, as_stop_step=False)
                body = llm_event.chat_messages[-1].content or ""
                replies.append(
                    (
                        classification_ref,
                        ReplyComposer.compose_from_parsed(parsed, from_address=imap_config.username, body=body),
                    )
                )
        return replies

    @staticmethod
    async def _reparse_archived(
        ref: MailClassificationRef,
        imap_config: ImapClientConfig,
        topic: AgentInstanceTopic,
    ) -> ParsedMessage:
        """Rebuild the parsed message from its archived bytes — the threading headers come from here, not the event."""
        raw = await MailStore.load_message(ref.original_message, agent_class=topic.agent_class, agent_id=topic.agent_id)
        return MailParser.parse_message(
            ref.message_id,
            email.message_from_bytes(raw, policy=default_policy),
            imap_config.max_body_bytes,
            imap_config.max_attachment_bytes,
            raw=b"",
        )

    @staticmethod
    async def _extracted_attachments(
        ref: MailClassificationRef,
        draft: DraftEmailSettings,
        topic: AgentInstanceTopic,
        displayer: EventDisplayer,
    ) -> list[ExtractedAttachment]:
        """Read the message's attachments when the admin asked for it; otherwise report none at all.

        With the toggle off the attachments are not even named in the prompt: the admin opted out of the model
        knowing about them, and listing files it cannot read only invites it to speculate.
        """
        if not draft.include_attachments or not ref.attachments:
            return []

        extracted = await AttachmentTextExtractor.extract(
            ref.attachments, draft, agent_class=topic.agent_class, agent_id=topic.agent_id
        )
        for attachment in extracted:
            if attachment.outcome is not AttachmentOutcome.TEXT:
                await displayer.display_thought(f"Attachment {attachment.inventory_line}")
        return extracted

    @staticmethod
    def _validate(
        classification: EmailClassificationSettings,
        draft: DraftEmailSettings,
        inbox_folder: str,
    ) -> None:
        """Fail the run rather than silently filing everything into the fallback folder, or drafting into the inbox.

        The drafting checks run here, before the first fetch, even though drafting happens at the very end: a run that
        classified and filed a whole batch at full model cost and only then discovered its drafts folder is
        unusable has wasted all of it.
        """
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

        if not draft.enable_draft:
            return

        if not any(category.draft_reply for category in classification.categories):
            raise ValueError(
                "reply drafting is enabled but no category is set to get a drafted reply — either tick a category or "
                "turn drafting off, rather than paying for a drafting pass that can never produce anything"
            )

        # A draft appended into the inbox arrives unread, so the next run classifies and files the agent's own
        # draft — and drafts a reply to it. Same class of unterminating loop as an inbox-equal target folder above,
        # and reachable the same way, by a typo in a free-text folder name.
        if draft.drafts_folder == inbox_folder:
            raise ValueError(
                f"drafts_folder equals the inbox folder {inbox_folder!r} — every draft would be classified and "
                "replied to on the following run"
            )
        if draft.drafts_folder in {*folders, classification.fallback_folder}:
            raise ValueError(
                f"drafts_folder {draft.drafts_folder!r} is also a category or fallback folder — drafts and filed "
                "mail would be indistinguishable in it"
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

        Holding the mailbox is the caller's heartbeat, not this loop's business: renewing per message here would
        leave the fetch and the filing either side of it unrenewed, which is how a lease sized for classification
        alone lapses on a slow mailbox.
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
