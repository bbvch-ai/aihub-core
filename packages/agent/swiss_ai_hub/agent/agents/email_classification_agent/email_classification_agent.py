import email
import logging
from collections import Counter
from collections.abc import Callable
from email.policy import default as default_policy
from typing import ClassVar

from llama_index.core.base.llms.types import ChatMessage, MessageRole
from llama_index.core.llms import LLM
from redis.asyncio import Redis
from swiss_ai_hub.core.auth import UserIdentity
from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import (
    AgentInTheLoop,
    CronStartEvent,
    MailBatchClassifiedEvent,
    MailBatchDraftedEvent,
    MailClassificationRef,
    RAGFailureStopEvent,
    RAGStartEvent,
    StopEvent,
    UnreadMailListedEvent,
)
from swiss_ai_hub.core.generative_ai import LLMConfig
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.imap import DraftEmailSettings, EmailClassificationSettings, ImapClientConfig
from swiss_ai_hub.core.topics import AgentInstanceTopic

from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.agents.email_classification_agent.configs.email_classification_agent_config import (
    EmailClassificationAgentConfig,
)
from swiss_ai_hub.agent.agents.email_classification_agent.configs.knowledge_delegation_config import (
    KnowledgeDelegationConfig,
)
from swiss_ai_hub.agent.agents.email_classification_agent.events.classify_mail_start_event import (
    ClassifyMailStartEvent,
)
from swiss_ai_hub.agent.agents.email_classification_agent.events.grounded_drafts_requested_event import (
    GroundedDraftsRequestedEvent,
)
from swiss_ai_hub.agent.agents.email_classification_agent.knowledge_namespace_resolver import (
    KnowledgeNamespaceResolver,
)
from swiss_ai_hub.agent.agents.email_classification_agent.mail_classifier import (
    CategoryVerdict,
    ClassificationOutcome,
    MailClassifier,
)
from swiss_ai_hub.agent.context.run.run_context import RunContext
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
from swiss_ai_hub.agent.workflow.decorators.precondition import precondition
from swiss_ai_hub.agent.workflow.decorators.step import step

logger = logging.getLogger(__name__)

# RunContext key holding {AgentInTheLoopRequestEvent.event_id: IMAP uid} for this run's delegated drafts.
GROUNDED_REQUEST_INDEX_KEY = "grounded_draft_requests"


@precondition()
async def all_delegated_drafts_returned(
    event: GroundedDraftsRequestedEvent,
    answers: list[AgentInTheLoop.response | AgentInTheLoop.exception],
) -> bool:
    """Hold the drafting step until every delegated RAG run has come back, one way or the other.

    The engine's fan-out join, `FixedList(T, N)`, bakes N into a class at import time, and the number of classified
    messages is only known at runtime — so a `list[...]` parameter plus this precondition is the join. A `list[...]`
    re-executes its step on every arrival, and without the wait each answer would append its own draft on its own
    IMAP connection.

    Counted over *distinct* request ids, and never with `==`. JetStream delivery is at-least-once, so a redelivered
    answer is an ordinary event: a raw count would overshoot N and, with `==`, wedge the run at exactly the point it
    was supposed to finish.
    """
    return len({answer.request_event_id for answer in answers}) >= event.grounded_count


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
        self._validate(
            classification,
            draft,
            imap_config.inbox_folder,
            agent_config.drafting_llm.token_counter,
            agent_config.knowledge_delegation,
        )
        # Separate from `_validate` because it reads the knowledge catalogue and the rest is pure config. Still runs
        # before the first fetch: a collection named by a typo must fail the run here, not after the whole batch has
        # been classified, filed and paid for, with the drafts unrecoverable because filing already consumed the mail.
        # Gated on `enable_draft` for the same reason `_validate_grounding` is, and to keep a paused deployment from
        # paying a catalogue round trip per run for a lookup nothing will use.
        if draft.enable_draft:
            await KnowledgeNamespaceResolver.validate(classification)
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
        # Counted off the verdicts, not off `classified`: a decline and a failure both leave `category` empty, so
        # counting refs would fold every failure into fallback_count and report an outage as ordinary uncertainty.
        fallback_count = sum(1 for verdict in verdicts if verdict.outcome is ClassificationOutcome.DECLINED)
        failed_count = sum(1 for verdict in verdicts if verdict.outcome is ClassificationOutcome.FAILED)
        logger.info(
            "[classify] filed %d message(s): %s, fallback=%d, failed=%d",
            len(classified),
            dict(per_category),
            fallback_count,
            failed_count,
        )
        return MailBatchClassifiedEvent(
            source_folder=imap_config.inbox_folder,
            count=len(classified),
            per_category=dict(per_category),
            fallback_count=fallback_count,
            failed_count=failed_count,
            classified=classified,
        )

    @step(
        name=AgentLocaleString.from_i18n_path("agent.email_classification_agent.steps.request_grounded_drafts.name"),
        icon="mage:book-open",
    )
    async def request_grounded_drafts_step(
        self,
        event: MailBatchClassifiedEvent,
        agent_config: EmailClassificationAgentConfig,
        imap_config: ImapClientConfig,
        classification: EmailClassificationSettings,
        draft: DraftEmailSettings,
        topic: AgentInstanceTopic,
        run_context: RunContext,
        displayer: EventDisplayer,
        t: LocaleHandler,
        redis: Redis,
        user: UserIdentity | None = None,
    ) -> list[GroundedDraftsRequestedEvent | AgentInTheLoop.request] | MailBatchDraftedEvent:
        """Ask the configured RAG agent to answer each classified message from its own category's collection.

        One delegated run per message, not one per batch: retrieval is only precise because each message is scoped to
        the single collection its category names, and a shared run could not be scoped to more than one of them.

        The delegation exists because a reply written from the message alone can only acknowledge it. The RAG agent
        already owns retrieval, reranking, the context-sufficiency guard and the answer prompt; this blueprint
        contributes the one thing that agent cannot know, which is which collection answers this particular message —
        and that is exactly what classification just decided.

        The prompt handed over is the same one the ungrounded path would have used, `DraftPromptBuilder` and all, so
        the token budget and the attachment handling are identical either way and a category can be switched between
        the two without its drafts changing shape.

        Runs with nothing to delegate finish the drafting here rather than emitting a marker nobody will answer:
        `collect_and_draft_step` waits on delegated answers, and with none due it could never fire.
        """
        to_draft = self._drafting_batch(event, classification, draft)
        grounded, ungrounded = self._split_by_grounding(to_draft, classification)

        if not grounded:
            await self._report_nothing_to_ground(event, to_draft, classification, draft, displayer)
            return await self._append_all_drafts(
                classified=event,
                grounded=[],
                ungrounded=ungrounded,
                bodies_by_message_id={},
                agent_config=agent_config,
                imap_config=imap_config,
                draft=draft,
                topic=topic,
                displayer=displayer,
                redis=redis,
            )

        # Built once for the batch, exactly as the ungrounded path does it: it owns the token budget, and a budget
        # too small for its own system prompt must fail here rather than per message.
        builder = DraftPromptBuilder(
            draft.number_of_input_tokens, agent_config.drafting_llm.token_counter, draft.draft_prompt
        )
        requests = []
        request_index: dict[str, str] = {}
        for classification_ref in grounded:
            request = await self._delegate_one(
                classification_ref, classification, draft, agent_config, topic, builder, t, user
            )
            requests.append(request)
            request_index[request.event_id] = classification_ref.message_id

        # Keyed by request event id and held in RunContext rather than on the event: it maps mail identifiers for the
        # whole batch, and the marker event is persisted to the audit trail and streamed to the frontend. Same reason
        # the drafting chain reads bodies back from the S3 archive instead of carrying them.
        await run_context.set(GROUNDED_REQUEST_INDEX_KEY, request_index)

        logger.info(
            "[draft] delegated %d message(s) to %s/%s for grounding, %d drafted without retrieval",
            len(grounded),
            agent_config.knowledge_delegation.rag_agent.agent_class,
            agent_config.knowledge_delegation.rag_agent.agent_id,
            len(ungrounded),
        )
        await displayer.display_thought(
            f"Looking up answers for {len(grounded)} message(s) in the knowledge base for their categories."
        )
        return [
            GroundedDraftsRequestedEvent(
                grounded_count=len(grounded),
                ungrounded_count=len(ungrounded),
                skipped_count=event.count - len(to_draft),
            ),
            *requests,
        ]

    @step(
        name=AgentLocaleString.from_i18n_path("agent.email_classification_agent.steps.collect_and_draft.name"),
        icon="mage:pen",
        precondition=all_delegated_drafts_returned,
    )
    async def collect_and_draft_step(
        self,
        event: GroundedDraftsRequestedEvent,
        classified: MailBatchClassifiedEvent,
        answers: list[AgentInTheLoop.response | AgentInTheLoop.exception],
        agent_config: EmailClassificationAgentConfig,
        imap_config: ImapClientConfig,
        classification: EmailClassificationSettings,
        draft: DraftEmailSettings,
        topic: AgentInstanceTopic,
        run_context: RunContext,
        displayer: EventDisplayer,
        redis: Redis,
    ) -> MailBatchDraftedEvent:
        """Turn every delegated answer into a threaded draft and append the whole batch in one pass.

        Both outcome kinds arrive on one parameter because the join has to wait for all of them and a message whose
        delegation failed still gets a draft — see `_body_for`. A `list[...]` re-executes this step on every arrival,
        so the precondition is what makes it run once, when the last one lands.

        Reads each message back from the S3 archive rather than from IMAP or from the event, exactly as the
        single-step drafting chain did: the UID died with the `MOVE` that filed it, and a body has no business on an
        event that is persisted and streamed.

        Nothing is flagged as drafted. Filing already prevents a second run seeing this mail, so a flag would be
        written to a UID that no longer resolves.

        The agent still never sends. A draft is an IMAP `APPEND`; there is no SMTP path anywhere in the platform.
        """
        to_draft = self._drafting_batch(classified, classification, draft)
        grounded, ungrounded = self._split_by_grounding(to_draft, classification)
        request_index: dict[str, str] = await run_context.get(GROUNDED_REQUEST_INDEX_KEY, {})

        bodies_by_message_id = await self._bodies_from_answers(answers, request_index, draft, displayer)

        return await self._append_all_drafts(
            classified=classified,
            grounded=grounded,
            ungrounded=ungrounded,
            bodies_by_message_id=bodies_by_message_id,
            agent_config=agent_config,
            imap_config=imap_config,
            draft=draft,
            topic=topic,
            displayer=displayer,
            redis=redis,
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
    def _split_by_grounding(
        to_draft: list[MailClassificationRef],
        classification: EmailClassificationSettings,
    ) -> tuple[list[MailClassificationRef], list[MailClassificationRef]]:
        """Split the drafting batch into the messages answered from a collection and those answered from the mail
        alone.

        Grounding is per category rather than per agent so a customer can adopt it one category at a time: a
        `support_request` has documentation behind it worth retrieving, while a `thanking` mail has none and would
        only retrieve noise.
        """
        namespaces = {
            category.category: category.knowledge_namespace
            for category in classification.categories
            if category.knowledge_namespace
        }
        grounded = [ref for ref in to_draft if ref.category in namespaces]
        return grounded, [ref for ref in to_draft if ref.category not in namespaces]

    async def _delegate_one(
        self,
        ref: MailClassificationRef,
        classification: EmailClassificationSettings,
        draft: DraftEmailSettings,
        agent_config: EmailClassificationAgentConfig,
        topic: AgentInstanceTopic,
        builder: DraftPromptBuilder,
        t: LocaleHandler,
        user: UserIdentity | None,
    ) -> AgentInTheLoop.request:
        """One delegated RAG run for one message, scoped to its category's collection and nothing else."""
        category = next(item for item in classification.categories if item.category == ref.category)
        pairs = await KnowledgeNamespaceResolver.resolve(
            classification.knowledge_databases, category.knowledge_namespace
        )
        parsed = await self._reparse_archived(ref, agent_config.imap, topic)
        attachments = await self._extracted_attachments_for_delegation(ref, draft, topic)

        return AgentInTheLoop.invoke(
            agent_class=agent_config.knowledge_delegation.rag_agent.agent_class,
            agent_id=agent_config.knowledge_delegation.rag_agent.agent_id,
            start_event=RAGStartEvent(
                messages=[
                    ChatMessage(role=MessageRole.SYSTEM, content=draft.draft_prompt),
                    ChatMessage(role=MessageRole.USER, content=builder.build(parsed, attachments)),
                ],
                # Forwarded, never substituted: a scheduled run has no user, and the RAG agent skips its
                # user-memory steps rather than attributing this mailbox's memories to a shared identity.
                user=user,
                locale=t.locale,
                files=[],
                selected_namespaces=pairs,
            ),
            # `share_run_id=False` is the correctness constraint, not a preference: the response subscription is
            # keyed by the delegated run id, so sharing it would make every subscriber of this fan-out fire on every
            # delegate's answer and the batch could not be attributed at all. The other two are isolation — N
            # concurrent runs must not share one ThreadContext, nor interleave their streams into one display.
            share_run_id=False,
            share_thread_id=False,
            share_display_id=False,
            timeout_seconds=draft.grounding_timeout_seconds,
        )

    @staticmethod
    async def _extracted_attachments_for_delegation(
        ref: MailClassificationRef,
        draft: DraftEmailSettings,
        topic: AgentInstanceTopic,
    ) -> list[ExtractedAttachment]:
        """Attachment text for a delegated prompt, with the per-attachment reporting left out.

        The reporting belongs to a step that is about to write a draft; here the run has only asked a question, and a
        thought per attachment per message would bury the one line that says how many messages were delegated.
        """
        if not draft.include_attachments or not ref.attachments:
            return []
        return await AttachmentTextExtractor.extract(
            ref.attachments, draft, agent_class=topic.agent_class, agent_id=topic.agent_id
        )

    @staticmethod
    async def _bodies_from_answers(
        answers: list[AgentInTheLoop.response | AgentInTheLoop.exception],
        request_index: dict[str, str],
        draft: DraftEmailSettings,
        displayer: EventDisplayer,
    ) -> dict[str, str]:
        """Map each delegated answer back to the message it belongs to, keeping the first answer per delegation.

        Duplicates are dropped rather than trusted: JetStream delivery is at-least-once, so a redelivered answer is
        an ordinary event, not a second opinion.

        An answer whose request is not in the index is ignored. That cannot happen on this workflow — nothing else
        delegates — but the index is what makes the attribution safe, and silently drafting from an unattributable
        answer is exactly the way a reply ends up on the wrong message.
        """
        bodies: dict[str, str] = {}
        for answer in answers:
            message_id = request_index.get(answer.request_event_id)
            if message_id is None:
                logger.warning(
                    "[draft] delegated answer %s belongs to no message of this run — ignoring it",
                    answer.request_event_id,
                )
                continue
            if message_id in bodies:
                continue
            bodies[message_id] = await EmailClassificationAgent._body_for(answer, message_id, draft, displayer)
        return bodies

    @staticmethod
    async def _body_for(
        answer: AgentInTheLoop.response | AgentInTheLoop.exception,
        message_id: str,
        draft: DraftEmailSettings,
        displayer: EventDisplayer,
    ) -> str:
        """The draft body for one delegated answer — the answer itself, or the configured text saying why there is
        none.

        Every outcome yields a body, and that is the invariant the whole chain rests on: filing is this blueprint's
        only dedup, so a message that got no draft is filed, unflagged and never seen again. It would sit in neither
        the drafted nor the untouched state, and nothing downstream covers that.

        The two failure texts are kept apart because they are different facts. A run that retrieved nothing has told
        the reviewer something true about the knowledge base; a run that crashed has told them only that the
        machinery broke, and reporting an outage as an absence of knowledge is how a broken deployment reads as a
        working one.

        The model is never asked to write around an empty context. An ungrounded reply that reads like a grounded one
        is worse than an honest blank, because a reviewer skims it and sends it.
        """
        if answer.is_aitl_exception_event:
            logger.warning(
                "[draft] grounding uid=%s failed: %s — drafting the configured failure text instead",
                message_id,
                answer.exception_event.message,
            )
            await displayer.display_thought(
                "The knowledge lookup failed for one message — drafting the configured fallback text for it."
            )
            return draft.grounding_failed_draft

        # `getattr` rather than a plain attribute read: the field belongs to `RAGStopEvent`, and while the agent
        # selector only offers agents accepting `RAGStartEvent`, nothing forces such an agent to terminate with a
        # `RAGStopEvent`. Raising here would cost the whole batch its drafts *after* every delegation had succeeded,
        # which is the most expensive moment there is to fail.
        stop_event = answer.stop_event
        returned_answer = getattr(stop_event, "answer", None)
        if isinstance(stop_event, RAGFailureStopEvent) or not (returned_answer or "").strip():
            reason = stop_event.reason if isinstance(stop_event, RAGFailureStopEvent) else "no usable answer"
            logger.info(
                "[draft] uid=%s could not be grounded (%s) — drafting the no-information text", message_id, reason
            )
            await displayer.display_thought(
                "Nothing in the knowledge base answers one message — drafting the configured fallback text for it."
            )
            return draft.no_information_draft

        return returned_answer

    async def _append_all_drafts(
        self,
        classified: MailBatchClassifiedEvent,
        grounded: list[MailClassificationRef],
        ungrounded: list[MailClassificationRef],
        bodies_by_message_id: dict[str, str],
        agent_config: EmailClassificationAgentConfig,
        imap_config: ImapClientConfig,
        draft: DraftEmailSettings,
        topic: AgentInstanceTopic,
        displayer: EventDisplayer,
        redis: Redis,
    ) -> MailBatchDraftedEvent:
        """Compose whatever still needs composing, then append the whole batch on one connection.

        Both entry points end here so there is exactly one place that appends and exactly one that emits
        `MailBatchDraftedEvent` — which is what keeps `finish_drafting_step` the single terminal step, and the lease
        release with it.
        """
        if not grounded and not ungrounded:
            return MailBatchDraftedEvent(
                # A zero-count event rather than a bare StopEvent: `skipped_count` is the only record of mail this
                # agent declined to draft for, and a consumer counting it would otherwise see nothing at all for
                # exactly the batches where every message was skipped. The lease is not released here — emitting the
                # event makes `finish_drafting_step` the terminal step on every path, and the release travels with it.
                source_folder=imap_config.inbox_folder,
                count=0,
                skipped_count=classified.count,
            )

        lease = MailboxRunLease(redis)
        if not await lease.reacquire(topic.agent_class, topic.agent_id, topic.run_id):
            raise MailboxLeaseLostError(
                f"run {topic.run_id} could not take back the mailbox lease on {topic.agent_class}/{topic.agent_id} "
                f"— another run holds it, so this run appends nothing"
            )

        async with lease.heartbeat(topic.agent_class, topic.agent_id, topic.run_id):
            replies = [
                (
                    ref,
                    ReplyComposer.compose_from_parsed(
                        await self._reparse_archived(ref, imap_config, topic),
                        from_address=imap_config.username,
                        body=bodies_by_message_id[ref.message_id],
                    ),
                )
                for ref in grounded
                if ref.message_id in bodies_by_message_id
            ]
            if ungrounded:
                replies += await self._compose_all(ungrounded, agent_config, draft, imap_config, topic, displayer)

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
            skipped_count=classified.count - len(drafted),
            drafted=drafted,
        )

    @staticmethod
    async def _report_nothing_to_ground(
        event: MailBatchClassifiedEvent,
        to_draft: list[MailClassificationRef],
        classification: EmailClassificationSettings,
        draft: DraftEmailSettings,
        displayer: EventDisplayer,
    ) -> None:
        """Say why nothing was delegated, so a silent run is never ambiguous between 'off', 'nothing matched' and
        'nothing grounded'."""
        if not draft.enable_draft:
            logger.info("[draft] enable_draft=False — filed %d message(s), drafting none", event.count)
            await displayer.display_thought("Reply drafting is disabled — no drafts were written.")
            return

        if not to_draft:
            opted_in = sorted(category.category for category in classification.categories if category.draft_reply)
            logger.info("[draft] no message in this batch belongs to a drafting category %s", opted_in)
            await displayer.display_thought(
                f"No mail in this run belongs to a category that gets a drafted reply ({', '.join(opted_in)})."
                if opted_in
                else "No category is set to get a drafted reply — no drafts were written."
            )
            return

        logger.info("[draft] no message in this batch belongs to a grounded category — drafting from the mail alone")
        await displayer.display_thought(
            f"No category in this run is grounded in a knowledge collection — drafting {len(to_draft)} reply/replies "
            "from the messages alone."
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
                reply = await self._compose_one(
                    classification_ref, builder, draft, imap_config, topic, displayer, llm, llm_config
                )
                if reply is not None:
                    replies.append((classification_ref, reply))
        return replies

    @staticmethod
    async def _compose_one(
        ref: MailClassificationRef,
        builder: DraftPromptBuilder,
        draft: DraftEmailSettings,
        imap_config: ImapClientConfig,
        topic: AgentInstanceTopic,
        displayer: EventDisplayer,
        llm: LLM,
        llm_config: LLMConfig,
    ) -> ComposedReply | None:
        """Draft one reply, or report that this message gets none. Never raises.

        The same trade as `_is_archived`, for a stronger reason: by the time drafting runs the whole batch is already
        filed, and `do_draft_replies` appends only after this loop finishes — so a raise here costs every *other*
        message its draft while changing nothing about the one that failed. Unlike a classification failure there is
        nothing to route: the message is already where it belongs, it simply has no draft, and the next run will not
        see it again.
        """
        try:
            parsed = await EmailClassificationAgent._reparse_archived(ref, imap_config, topic)
            attachments = await EmailClassificationAgent._extracted_attachments(ref, draft, topic, displayer)
            await displayer.display_thought(f"Drafting a reply to: {parsed.subject}")
            messages = [
                ChatMessage(role=MessageRole.SYSTEM, content=draft.draft_prompt),
                ChatMessage(role=MessageRole.USER, content=builder.build(parsed, attachments)),
            ]
            llm_event = await displayer.display_llm_stream(llm_config, llm, messages, as_stop_step=False)
            body = llm_event.chat_messages[-1].content or ""
            return ReplyComposer.compose_from_parsed(parsed, from_address=imap_config.username, body=body)
        except Exception:
            logger.warning(
                "[draft] could not draft a reply to uid=%s — skipping it, not the batch", ref.message_id, exc_info=True
            )
            await displayer.display_thought(
                f"Could not draft a reply to {ref.subject} — it is filed correctly and the other drafts are unaffected."
            )
            return None

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
        token_counter: Callable[[str], list[int]],
        knowledge_delegation: KnowledgeDelegationConfig | None = None,
    ) -> None:
        """Fail the run rather than silently filing everything into the fallback folder, or drafting into the inbox.

        The drafting checks run here, before the first fetch, even though drafting happens at the very end: a run that
        classified and filed a whole batch at full model cost and only then discovered its drafts folder is
        unusable has wasted all of it.
        """
        EmailClassificationAgent._validate_taxonomy(classification, inbox_folder)
        EmailClassificationAgent._validate_drafting(classification, draft, inbox_folder, token_counter)
        EmailClassificationAgent._validate_grounding(classification, draft, knowledge_delegation)

    @staticmethod
    def _validate_taxonomy(classification: EmailClassificationSettings, inbox_folder: str) -> None:
        """The folders mail is filed into must be distinct from each other and from the inbox."""
        if not classification.categories:
            raise ValueError("no categories are configured — the agent has nothing to classify into")
        if not classification.fallback_folder:
            raise ValueError("fallback_folder is empty — mail the model is unsure about would have nowhere to go")
        if not classification.failure_folder:
            raise ValueError("failure_folder is empty — mail the classifier failed on would have nowhere to go")

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
        if classification.failure_folder in folders:
            raise ValueError(
                f"failure_folder {classification.failure_folder!r} is also a category folder — a message the "
                "classifier never reached a verdict on would be indistinguishable from one it placed there"
            )
        if classification.failure_folder == classification.fallback_folder:
            raise ValueError(
                f"failure_folder {classification.failure_folder!r} equals the fallback folder — an operator could "
                "not tell mail the model deliberately declined from mail it never read, which is the whole reason "
                "the two are kept apart"
            )

        # Filing out of the inbox is the only dedup this agent has, and a target equal to the inbox defeats it.
        # On the COPY + UID EXPUNGE path the original is replaced by a fresh unread copy in the same folder, so the
        # next run classifies the copy, archives it again, and repeats without termination. Folder names are
        # admin-entered free text, so this is reachable by a typo rather than only by misuse.
        if inbox_folder in {*folders, classification.fallback_folder, classification.failure_folder}:
            raise ValueError(
                f"a target folder equals the inbox folder {inbox_folder!r} — filed mail would stay unread in the "
                "inbox and be reprocessed on every run"
            )

    @staticmethod
    def _validate_drafting(
        classification: EmailClassificationSettings,
        draft: DraftEmailSettings,
        inbox_folder: str,
        token_counter: Callable[[str], list[int]],
    ) -> None:
        """Reject a drafting setup that cannot produce a draft, before the run spends anything on classification."""
        if not draft.enable_draft:
            return

        folders = [category.imap_folder for category in classification.categories]

        # Constructing the builder is the check: it is the thing that knows whether the configured budget survives
        # the system prompt, and a budget that cannot is only discovered at drafting time otherwise — after the whole
        # batch has been classified and filed, with the drafts unrecoverable.
        DraftPromptBuilder(draft.number_of_input_tokens, token_counter, draft.draft_prompt)

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
        if draft.drafts_folder in {*folders, classification.fallback_folder, classification.failure_folder}:
            raise ValueError(
                f"drafts_folder {draft.drafts_folder!r} is also a category or fallback folder — drafts and filed "
                "mail would be indistinguishable in it"
            )

    @staticmethod
    def _validate_grounding(
        classification: EmailClassificationSettings,
        draft: DraftEmailSettings,
        knowledge_delegation: KnowledgeDelegationConfig | None,
    ) -> None:
        """Reject a grounding setup that cannot produce a grounded draft, before the run spends anything.

        Skipped entirely when drafting is off, mirroring `_validate_drafting`: `_drafting_batch` returns nothing in
        that state, so grounding cannot execute and must not be able to fail a run either. Otherwise an admin who
        configured grounding and later paused drafting — or whose collection was deleted while it was paused — would
        have every classification run die on a feature that cannot run.

        Beyond that, only reached when a category actually names a collection: grounding is opt-in per category, and a
        deployment that drafts from the message alone must keep working with no knowledge agent configured at all.
        """
        if not draft.enable_draft:
            return

        grounded = [category for category in classification.categories if category.knowledge_namespace]
        if not grounded:
            return

        if knowledge_delegation is None:
            raise ValueError(
                f"categories {[category.category for category in grounded]} are grounded in a knowledge collection "
                "but no knowledge agent is configured — their replies have nothing to retrieve from"
            )
        if not classification.knowledge_databases:
            raise ValueError(
                "a category names a knowledge collection but no knowledge database is configured — a collection "
                "name alone does not identify anything to retrieve from"
            )

        # Checked here rather than left to the form: a blank fallback would only be discovered by the message that
        # needed it, which is the one message nobody is watching for.
        if not draft.no_information_draft.strip() or not draft.grounding_failed_draft.strip():
            raise ValueError(
                "both fallback draft texts must be set when a category is grounded — a message retrieval could not "
                "answer must still get a draft, or it stays filed with no draft and is never looked at again"
            )

        # `draft_reply` is what puts a message in the drafting batch at all, so a grounded category that is not
        # opted in retrieves nothing and would have the admin looking for drafts that were never due.
        not_opted_in = [category.category for category in grounded if not category.draft_reply]
        if not_opted_in:
            raise ValueError(
                f"categories {not_opted_in} name a knowledge collection but are not set to get a drafted reply — "
                "either tick their reply toggle or clear their collection"
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
                verdict = await MailClassifier.classify(mail.parsed, classification, llm, llm_config.token_counter)
                logger.info(
                    "[classify] uid=%s subject=%r -> %s (%s)",
                    mail.parsed.message_id,
                    mail.parsed.subject,
                    verdict.target_folder(classification),
                    verdict.outcome,
                )
                await self._report_verdict(mail.parsed.subject, verdict, classification, displayer)
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
