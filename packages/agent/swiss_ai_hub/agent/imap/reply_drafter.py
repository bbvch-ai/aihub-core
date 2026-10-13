import logging

from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.core.auth import UserIdentity
from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import DraftedReplyRef
from swiss_ai_hub.core.imap import DraftEmailSettings, ImapClientConfig, ParsedMessage

from swiss_ai_hub.agent.imap.composed_reply import ComposedReply
from swiss_ai_hub.agent.imap.imap_client import ImapClientFactory
from swiss_ai_hub.agent.imap.reply_composer import ReplyComposer

logger = logging.getLogger(__name__)


class ReplyDrafter:
    """Drafts LLM replies to a batch of mail: read in one connection, compose with none held, persist in another."""

    @staticmethod
    async def read_candidates(
        imap_config: ImapClientConfig, draft: DraftEmailSettings
    ) -> tuple[str, list[ParsedMessage]]:
        """Read the undrafted batch (read-only, ``BODY.PEEK``) in a short-lived connection, so the IMAP socket is not
        held open across the LLM calls that follow — an idle socket gets dropped by many servers mid-batch."""
        async with ImapClientFactory.create(imap_config) as client:
            drafted_flag, candidates = await client.list_undrafted(draft.source_folder, draft.batch_size)
            parsed = [
                await client.fetch_message(candidate.message_id, folder=draft.source_folder) for candidate in candidates
            ]
        return drafted_flag, parsed

    @staticmethod
    async def compose_reply(
        parsed: ParsedMessage,
        draft: DraftEmailSettings,
        imap_config: ImapClientConfig,
        displayer: EventDisplayer,
        user: UserIdentity | None,
    ) -> ComposedReply:
        """Draft the reply body with the LLM (no IMAP connection held) and wrap it in a threaded envelope.

        Inbound mail is untrusted and enters the LLM prompt; the platform's Presidio guard anonymizes PII at the LLM
        gateway, so this step adds no sanitisation of its own.
        """
        await displayer.display_thought(f"Drafting a reply to: {parsed.subject}")
        messages = [
            ChatMessage(role=MessageRole.SYSTEM, content=draft.draft_prompt),
            ChatMessage(
                role=MessageRole.USER,
                content=ReplyDrafter._render_original(parsed.sender, parsed.subject, parsed.body_text),
            ),
        ]
        llm_config = draft.llm
        async with llm_config.cost_reporting_llm(displayer, user=user) as llm:
            llm_event = await displayer.display_llm_stream(llm_config, llm, messages, as_stop_step=False)
        body = llm_event.chat_messages[-1].content or ""
        return ReplyComposer.compose_from_parsed(parsed, from_address=imap_config.username, body=body)

    @staticmethod
    async def persist(
        imap_config: ImapClientConfig,
        draft: DraftEmailSettings,
        drafted_flag: str,
        replies: list[tuple[ParsedMessage, ComposedReply]],
    ) -> list[DraftedReplyRef]:
        """Append each draft then flag its source (at-least-once: append before flag), in a fresh connection opened
        after all LLM work so the socket is never idle mid-stream."""
        drafted: list[DraftedReplyRef] = []
        async with ImapClientFactory.create(imap_config) as client:
            for parsed, reply in replies:
                resolved_folder, draft_uid = await client.append_draft(draft.drafts_folder, reply.raw)
                await client.mark_drafted(draft.source_folder, parsed.message_id, drafted_flag)
                logger.info(
                    "[imap] draft_batch_step: drafted uid=%s -> %r (draft_uid=%s), marked with %s",
                    parsed.message_id,
                    resolved_folder,
                    draft_uid,
                    drafted_flag,
                )
                drafted.append(
                    DraftedReplyRef(
                        source_uid=parsed.message_id,
                        drafts_folder=resolved_folder,
                        draft_uid=draft_uid,
                        in_reply_to=reply.in_reply_to,
                        subject=reply.subject,
                        recipient=reply.recipient,
                    )
                )
        return drafted

    @staticmethod
    def _render_original(sender: str, subject: str, body_text: str | None) -> str:
        return f"From: {sender}\nSubject: {subject}\n\n{body_text or ''}"
