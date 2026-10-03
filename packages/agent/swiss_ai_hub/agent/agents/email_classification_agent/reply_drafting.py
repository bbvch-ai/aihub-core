import email
import logging
from collections import Counter
from email.policy import default as default_policy

from llama_index.core.base.llms.types import ChatMessage, MessageRole
from llama_index.core.llms import LLM
from redis.asyncio import Redis
from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import (
    MailBatchClassifiedEvent,
    MailBatchDraftedEvent,
    MailClassificationRef,
)
from swiss_ai_hub.core.generative_ai import LLMConfig
from swiss_ai_hub.core.imap import (
    DraftEmailSettings,
    EmailClassificationSettings,
    ImapClientConfig,
    MailParser,
    ParsedMessage,
)
from swiss_ai_hub.core.topics import AgentInstanceTopic

from swiss_ai_hub.agent.agents.email_classification_agent.configs.email_classification_agent_config import (
    EmailClassificationAgentConfig,
)
from swiss_ai_hub.agent.agents.email_classification_agent.configs.knowledge_delegation_config import (
    KnowledgeDelegationConfig,
)
from swiss_ai_hub.agent.imap.attachment_text_extractor import AttachmentTextExtractor
from swiss_ai_hub.agent.imap.composed_reply import ComposedReply
from swiss_ai_hub.agent.imap.draft_prompt_builder import DraftPromptBuilder
from swiss_ai_hub.agent.imap.extracted_attachment import AttachmentOutcome, ExtractedAttachment
from swiss_ai_hub.agent.imap.mail_store import MailStore
from swiss_ai_hub.agent.imap.mailbox_lease_lost_error import MailboxLeaseLostError
from swiss_ai_hub.agent.imap.mailbox_run_lease import MailboxRunLease
from swiss_ai_hub.agent.imap.reply_composer import ReplyComposer
from swiss_ai_hub.agent.imap.step_functions import (
    do_draft_replies,
)

logger = logging.getLogger(__name__)


class ReplyDrafting:
    """Which filed messages get a reply draft, how the local ones are composed, and the one place drafts are
    appended."""

    @staticmethod
    def drafting_batch(
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
        return [ref for ref in event.classified if ref.category in opted_in and ReplyDrafting._is_archived(ref)]

    @staticmethod
    def _is_archived(ref: MailClassificationRef) -> bool:
        if ref.original_message:
            return True
        logger.warning("[draft] uid=%s has no archived original — cannot draft a reply to it, skipping", ref.message_id)
        return False

    @staticmethod
    def split_by_grounding(
        to_draft: list[MailClassificationRef],
        knowledge_delegation: KnowledgeDelegationConfig | None,
    ) -> tuple[list[MailClassificationRef], list[MailClassificationRef]]:
        """Split the drafting batch into the messages answered from knowledge and those answered from the mail alone.

        With a knowledge agent configured every drafted message is answered from it: a category naming collections is
        narrowed to them, a category naming none is answered from everything the agent retrieves from. With no
        knowledge agent there is nothing to delegate to, so the whole batch takes the local path, which is what keeps
        a deployment with no RAG agent at all working.
        """
        if knowledge_delegation is None:
            return [], to_draft
        return to_draft, []

    @staticmethod
    async def append_all_drafts(
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
                        await ReplyDrafting.reparse_archived(ref, imap_config, topic),
                        from_address=imap_config.username,
                        body=bodies_by_message_id[ref.message_id],
                    ),
                )
                for ref in grounded
                if ref.message_id in bodies_by_message_id
            ]
            if ungrounded:
                replies += await ReplyDrafting._compose_all(
                    ungrounded, agent_config, draft, imap_config, topic, displayer
                )

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
    async def report_nothing_to_ground(
        event: MailBatchClassifiedEvent,
        to_draft: list[MailClassificationRef],
        classification: EmailClassificationSettings,
        draft: DraftEmailSettings,
        knowledge_delegation: KnowledgeDelegationConfig | None,
        displayer: EventDisplayer,
    ) -> None:
        """Say why nothing was delegated, so a silent run is never ambiguous between 'off', 'nothing matched' and
        'no knowledge agent'."""
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

        if knowledge_delegation is None:
            logger.info(
                "[draft] no knowledge agent is configured — drafting %d message(s) from the mail alone", len(to_draft)
            )
            await displayer.display_thought(
                f"No knowledge agent is configured — drafting {len(to_draft)} reply/replies from the messages alone."
            )
            return

    @staticmethod
    async def _compose_all(
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
                reply = await ReplyDrafting._compose_one(
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
            parsed = await ReplyDrafting.reparse_archived(ref, imap_config, topic)
            attachments = await ReplyDrafting._extracted_attachments(ref, draft, topic, displayer)
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
    async def reparse_archived(
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
