import logging

from llama_index.core.base.llms.types import ChatMessage, MessageRole
from llama_index.core.llms import LLM
from swiss_ai_hub.core.auth import UserIdentity
from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import (
    AgentInTheLoop,
    MailClassificationRef,
    RAGFailureStopEvent,
    RAGStartEvent,
    RefusalStopEvent,
)
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.imap import (
    DraftEmailSettings,
    EmailClassificationSettings,
    ParsedMessage,
)
from swiss_ai_hub.core.topics import AgentInstanceTopic

from swiss_ai_hub.agent.agents.email_classification_agent.configs.email_classification_agent_config import (
    EmailClassificationAgentConfig,
)
from swiss_ai_hub.agent.agents.email_classification_agent.reply_drafting import ReplyDrafting
from swiss_ai_hub.agent.imap.attachment_text_extractor import AttachmentTextExtractor
from swiss_ai_hub.agent.imap.draft_prompt_builder import DraftPromptBuilder
from swiss_ai_hub.agent.imap.extracted_attachment import ExtractedAttachment
from swiss_ai_hub.agent.imap.mail_language_detector import MailLanguageDetector

logger = logging.getLogger(__name__)


class GroundingDelegation:
    """Hands each drafted message to the knowledge agent, and turns the answers back into draft bodies."""

    @staticmethod
    async def delegate_one(
        ref: MailClassificationRef,
        classification: EmailClassificationSettings,
        draft: DraftEmailSettings,
        agent_config: EmailClassificationAgentConfig,
        topic: AgentInstanceTopic,
        builder: DraftPromptBuilder,
        llm: LLM,
        t: LocaleHandler,
        user: UserIdentity | None,
    ) -> AgentInTheLoop.request:
        """One delegated RAG run for one message, scoped to its category's collections, in the message's language.

        A category that names none is sent an empty selection, which `narrow_retrievers` reads as the delegate's whole
        scope. A selection switched on but left empty would read the same way while looking narrowed, so
        `MailTriageValidator._validate_grounding` rejects that state up front rather than letting it reach a run.
        """
        category = next(item for item in classification.categories if item.category == ref.category)
        parsed = await ReplyDrafting.reparse_archived(ref, agent_config.imap, topic)
        attachments = await GroundingDelegation._extracted_attachments_for_delegation(ref, draft, topic)
        draft_prompt, locale = await GroundingDelegation._in_reply_language(draft.draft_prompt, parsed, llm, t)

        return AgentInTheLoop.invoke(
            agent_class=agent_config.knowledge_delegation.rag_agent.agent_class,
            agent_id=agent_config.knowledge_delegation.rag_agent.agent_id,
            start_event=RAGStartEvent(
                messages=[
                    ChatMessage(role=MessageRole.SYSTEM, content=draft_prompt),
                    ChatMessage(role=MessageRole.USER, content=builder.build(parsed, attachments)),
                ],
                # Forwarded, never substituted: a scheduled run has no user, and the RAG agent skips its
                # user-memory steps rather than attributing this mailbox's memories to a shared identity.
                user=user,
                locale=locale,
                # A draft is plain text in the user's mailbox; citation markers would reach the recipient.
                cite_sources=False,
                files=[],
                selected_namespaces=category.knowledge_namespaces or [],
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
    async def _in_reply_language(
        draft_prompt: str, parsed: ParsedMessage, llm: LLM, t: LocaleHandler
    ) -> tuple[str, str]:
        """The drafting prompt and delegated locale for a reply in the language `parsed` is written in.

        Both, because either alone was not enough: the locale only picks the delegate's own system and context
        prompts, and the admin's drafting prompt — one language, fixed phrases — outweighed them. A language that
        cannot be detected keeps the prompt as written and the run's own locale.
        """
        locale = await MailLanguageDetector.detect(llm, parsed)
        if locale is None:
            return draft_prompt, t.locale
        return MailLanguageDetector.with_reply_language(draft_prompt, locale), locale

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
    async def bodies_from_answers(
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
            bodies[message_id] = await GroundingDelegation._body_for(answer, message_id, draft, displayer)
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
        if isinstance(stop_event, RAGFailureStopEvent | RefusalStopEvent) or not (returned_answer or "").strip():
            reason = (
                stop_event.reason
                if isinstance(stop_event, RAGFailureStopEvent | RefusalStopEvent)
                else "no usable answer"
            )
            logger.info(
                "[draft] uid=%s could not be grounded (%s) — drafting the no-information text", message_id, reason
            )
            await displayer.display_thought(
                "Nothing in the knowledge base answers one message — drafting the configured fallback text for it."
            )
            return draft.no_information_draft

        return returned_answer
