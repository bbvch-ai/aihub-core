import logging
from collections import Counter
from typing import ClassVar

from redis.asyncio import Redis
from swiss_ai_hub.core.auth import UserIdentity
from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import (
    AgentInTheLoop,
    CronStartEvent,
    MailBatchClassifiedEvent,
    MailBatchDraftedEvent,
    StopEvent,
    UnreadMailListedEvent,
)
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.imap import (
    DraftEmailSettings,
    EmailClassificationSettings,
    ImapClientConfig,
)
from swiss_ai_hub.core.topics import AgentInstanceTopic

from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.agents.email_classification_agent.configs.email_classification_agent_config import (
    EmailClassificationAgentConfig,
)
from swiss_ai_hub.agent.agents.email_classification_agent.events.classify_mail_start_event import (
    ClassifyMailStartEvent,
)
from swiss_ai_hub.agent.agents.email_classification_agent.events.grounded_drafts_requested_event import (
    GroundedDraftsRequestedEvent,
)
from swiss_ai_hub.agent.agents.email_classification_agent.grounding_delegation import GroundingDelegation
from swiss_ai_hub.agent.agents.email_classification_agent.knowledge_collection_validator import (
    KnowledgeCollectionValidator,
)
from swiss_ai_hub.agent.agents.email_classification_agent.mail_classifier import (
    ClassificationOutcome,
)
from swiss_ai_hub.agent.agents.email_classification_agent.mail_filer import MailFiler
from swiss_ai_hub.agent.agents.email_classification_agent.mail_triage_validator import MailTriageValidator
from swiss_ai_hub.agent.agents.email_classification_agent.reply_drafting import ReplyDrafting
from swiss_ai_hub.agent.context.run.run_context import RunContext
from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString
from swiss_ai_hub.agent.imap.draft_prompt_builder import DraftPromptBuilder
from swiss_ai_hub.agent.imap.mailbox_lease_lost_error import MailboxLeaseLostError
from swiss_ai_hub.agent.imap.mailbox_run_lease import MailboxRunLease
from swiss_ai_hub.agent.imap.step_functions import (
    do_fetch_and_archive,
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
        MailTriageValidator.validate(
            classification,
            draft,
            imap_config.inbox_folder,
            agent_config.drafting_llm.token_counter,
            agent_config.knowledge_delegation,
        )
        # Separate from `MailTriageValidator.validate` because it reads the knowledge catalogue and the rest is pure
        # config. Still runs before the first fetch: a collection deleted since the profile was saved must fail the
        # run here, not after the whole batch has been classified, filed and paid for, with the drafts unrecoverable
        # because filing already consumed the mail. Gated on `enable_draft` for the same reason the grounding
        # validation is, and to keep a paused deployment from paying a catalogue round trip per run for a lookup
        # nothing will use.
        if draft.enable_draft:
            await KnowledgeCollectionValidator.validate(classification)
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
            verdicts = await MailFiler.classify_all(fetched, agent_config, classification, displayer, user)

            # Checked here and not earlier because filing is the only phase that mutates the mailbox: a fetch or a
            # classification this run no longer owns has wasted time and money, but only filing can put two runs on
            # the same messages.
            if lease.lost:
                raise MailboxLeaseLostError(
                    f"run {topic.run_id} lost the mailbox lease on {topic.agent_class}/{topic.agent_id} before "
                    f"filing {len(fetched)} message(s) — another run holds it, so this run files nothing"
                )

            classified = await MailFiler.file_all(fetched, verdicts, imap_config, classification, displayer)

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
        to_draft = ReplyDrafting.drafting_batch(event, classification, draft)
        grounded, ungrounded = ReplyDrafting.split_by_grounding(to_draft, agent_config.knowledge_delegation)

        if not grounded:
            await ReplyDrafting.report_nothing_to_ground(
                event, to_draft, classification, draft, agent_config.knowledge_delegation, displayer
            )
            return await ReplyDrafting.append_all_drafts(
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
        async with agent_config.drafting_llm.cost_reporting_llm(displayer, user=user) as llm:
            for classification_ref in grounded:
                request = await GroundingDelegation.delegate_one(
                    classification_ref, classification, draft, agent_config, topic, builder, llm, t, user
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
        delegation failed still gets a draft — see `GroundingDelegation.bodies_from_answers`. A `list[...]`
        re-executes this step on every arrival, so the precondition is what makes it run once, when the last one lands.

        Reads each message back from the S3 archive rather than from IMAP or from the event, exactly as the
        single-step drafting chain did: the UID died with the `MOVE` that filed it, and a body has no business on an
        event that is persisted and streamed.

        Nothing is flagged as drafted. Filing already prevents a second run seeing this mail, so a flag would be
        written to a UID that no longer resolves.

        The agent still never sends. A draft is an IMAP `APPEND`; there is no SMTP path anywhere in the platform.
        """
        to_draft = ReplyDrafting.drafting_batch(classified, classification, draft)
        grounded, ungrounded = ReplyDrafting.split_by_grounding(to_draft, agent_config.knowledge_delegation)
        request_index: dict[str, str] = await run_context.get(GROUNDED_REQUEST_INDEX_KEY, {})

        bodies_by_message_id = await GroundingDelegation.bodies_from_answers(answers, request_index, draft, displayer)

        return await ReplyDrafting.append_all_drafts(
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
