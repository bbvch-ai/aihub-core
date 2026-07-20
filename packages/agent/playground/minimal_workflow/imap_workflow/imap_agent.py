import logging
from typing import ClassVar

from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import (
    DraftedReplyRef,
    MailBatchDraftedEvent,
    MailFetchedEvent,
    MailMovedEvent,
    StopEvent,
    UnreadMailListedEvent,
)
from swiss_ai_hub.core.imap import DraftEmailSettings, ImapClientConfig
from swiss_ai_hub.core.topics import AgentInstanceTopic

from playground.minimal_workflow.imap_workflow.events.draft_mail_start_event import DraftMailStartEvent
from playground.minimal_workflow.imap_workflow.events.read_mail_start_event import ReadMailStartEvent
from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString
from swiss_ai_hub.agent.imap.imap_client import ImapClientFactory
from swiss_ai_hub.agent.imap.mail_attachment_store import MailAttachmentStore
from swiss_ai_hub.agent.imap.reply_composer import ReplyComposer
from swiss_ai_hub.agent.workflow.decorators.step import step

logger = logging.getLogger(__name__)


class ImapAgent(Agent):
    """Demonstrator for the IMAP capability with two independent, separately-triggered chains.

    - **Read + move** (``ReadMailStartEvent``): list unread inbox mail → fetch the first message with attachments →
      optionally move it to the processed folder → finish.
    - **Draft** (``DraftMailStartEvent``): read a batch of not-yet-drafted messages from the configured source folder →
      draft an LLM reply for each and append it to the drafts folder → mark each source message as drafted (leaving it
      unread) → finish.

    Non-conversational (like RetrievalAgent): triggered programmatically (e.g. by a scheduler), configured via its form,
    not exposed in the chat UI.
    """

    name: ClassVar[AgentLocaleString] = AgentLocaleString(
        en="IMAP Agent", de="IMAP-Agent", fr="Agent IMAP", it="Agente IMAP"
    )
    description: ClassVar[AgentLocaleString] = AgentLocaleString(
        en="Reads unread mail from an IMAP inbox, fetches a message with attachments, optionally files it away, and "
        "independently drafts replies for a batch of messages",
        de="Liest ungelesene E-Mails aus einem IMAP-Posteingang, ruft eine Nachricht mit Anhängen ab, legt sie "
        "optional ab und entwirft unabhängig Antworten für einen Stapel von Nachrichten",
        fr="Lit les e-mails non lus d'une boîte IMAP, récupère un message avec pièces jointes, le classe "
        "éventuellement, et rédige indépendamment des réponses pour un lot de messages",
        it="Legge le e-mail non lette da una casella IMAP, recupera un messaggio con allegati, lo archivia "
        "facoltativamente e redige autonomamente risposte per un lotto di messaggi",
    )
    icon: ClassVar[str] = "mage:inbox"

    @step(
        name=AgentLocaleString(en="List unread mail", de="Ungelesene E-Mails auflisten"),
        icon="mage:inbox",
    )
    async def list_unread_step(
        self,
        _event: ReadMailStartEvent,
        imap_config: ImapClientConfig,
    ) -> UnreadMailListedEvent:
        """Open the inbox and return header summaries of all unread messages."""
        logger.info(
            "[imap] list_unread_step: connecting to %s as %s, folder=%s",
            imap_config.host,
            imap_config.username,
            imap_config.inbox_folder,
        )
        async with ImapClientFactory.create(imap_config) as client:
            summaries = await client.list_unread()
        logger.info(
            "[imap] list_unread_step: found %d unread message(s): %s", len(summaries), [s.subject for s in summaries]
        )
        return UnreadMailListedEvent(messages=summaries)

    @step(
        name=AgentLocaleString(en="Fetch message", de="Nachricht abrufen"),
        icon="mage:email-opened",
    )
    async def fetch_mail_step(
        self,
        event: UnreadMailListedEvent,
        imap_config: ImapClientConfig,
        topic: AgentInstanceTopic,
        displayer: EventDisplayer,
    ) -> MailFetchedEvent | StopEvent:
        """Fetch the first unread message including body and attachments; stop early if the inbox is empty."""
        if not event.messages:
            logger.info("[imap] fetch_mail_step: inbox has no unread mail — stopping")
            await displayer.display_thought("No unread messages in the inbox.")
            return StopEvent()

        message_id = event.messages[0].message_id
        logger.info("[imap] fetch_mail_step: fetching message uid=%s", message_id)
        async with ImapClientFactory.create(imap_config) as client:
            parsed = await client.fetch_message(message_id)
        logger.info(
            "[imap] fetch_mail_step: fetched from=%s subject=%r date=%s attachments=%d body_len=%d",
            parsed.sender,
            parsed.subject,
            parsed.date,
            len(parsed.attachments),
            len(parsed.body_text or ""),
        )

        attachments = await MailAttachmentStore.store(
            parsed.attachments,
            agent_class=topic.agent_class,
            agent_id=topic.agent_id,
        )
        return MailFetchedEvent(
            message_id=parsed.message_id,
            sender=parsed.sender,
            subject=parsed.subject,
            date=parsed.date,
            body_text=parsed.body_text,
            rfc_message_id=parsed.rfc_message_id,
            references=parsed.references,
            reply_to=parsed.reply_to,
            attachments=attachments,
        )

    @step(
        name=AgentLocaleString(en="Move message", de="Nachricht verschieben"),
        icon="mage:folder-2",
    )
    async def move_mail_step(
        self,
        event: MailFetchedEvent,
        imap_config: ImapClientConfig,
        displayer: EventDisplayer,
    ) -> MailMovedEvent | StopEvent:
        """File the fetched message into the processed folder; stop the read/move run when moving is disabled."""
        if not imap_config.enable_move:
            logger.info(
                "[imap] move_mail_step: enable_move=False — leaving uid=%s in %s",
                event.message_id,
                imap_config.inbox_folder,
            )
            await displayer.display_thought("Moving is disabled — leaving the message in the inbox.")
            return StopEvent()
        if not imap_config.processed_folder:
            raise ValueError("enable_move is on but processed_folder is empty")

        logger.info(
            "[imap] move_mail_step: moving uid=%s from %s to %s",
            event.message_id,
            imap_config.inbox_folder,
            imap_config.processed_folder,
        )
        async with ImapClientFactory.create(imap_config) as client:
            await client.move_message(event.message_id, imap_config.processed_folder)
        logger.info("[imap] move_mail_step: moved uid=%s -> %s", event.message_id, imap_config.processed_folder)
        return MailMovedEvent(
            message_id=event.message_id,
            source_folder=imap_config.inbox_folder,
            target_folder=imap_config.processed_folder,
        )

    @step(
        name=AgentLocaleString(en="Finish", de="Abschliessen"),
        icon="mage:check",
    )
    async def finish_after_move_step(self, _event: MailMovedEvent) -> StopEvent:
        """Terminate the read/move run once the message has been (optionally) filed away."""
        logger.info("[imap] finish_after_move_step: read/move run complete")
        return StopEvent()

    @step(
        name=AgentLocaleString(en="Draft replies", de="Antworten entwerfen"),
        icon="mage:pen",
    )
    async def draft_batch_step(
        self,
        _event: DraftMailStartEvent,
        imap_config: ImapClientConfig,
        draft: DraftEmailSettings,
        displayer: EventDisplayer,
    ) -> MailBatchDraftedEvent | StopEvent:
        """Draft LLM replies for a batch of not-yet-drafted messages read from the configured source folder.

        Independent of the read/move chain: it lists up to ``batch_size`` messages in ``draft.source_folder`` that are
        not yet marked with the drafted flag (a custom keyword, or ``\\Answered`` on servers without keyword support),
        drafts a reply for each, appends it to the drafts folder, and then marks the source message drafted. Reads use
        ``BODY.PEEK`` and marking never sets ``\\Seen``, so the source mail stays unread. Ordering is at-least-once —
        the draft is appended before the source is flagged, so a crash re-drafts (a recoverable duplicate) rather than
        skipping. Inbound mail is untrusted and enters the LLM prompt; the Presidio guard covers the LLM path.
        """
        if not draft.enable_draft:
            logger.info("[imap] draft_batch_step: enable_draft=False — nothing to draft, stopping")
            await displayer.display_thought("Drafting is disabled — no replies were drafted.")
            return StopEvent()

        llm_config = draft.llm
        drafted: list[DraftedReplyRef] = []
        async with ImapClientFactory.create(imap_config) as client:
            drafted_flag = await client.resolve_drafted_flag(draft.source_folder)
            candidates = await client.list_undrafted(draft.source_folder, drafted_flag, draft.batch_size)
            logger.info(
                "[imap] draft_batch_step: %d undrafted message(s) in %s (flag=%s, batch_size=%d)",
                len(candidates),
                draft.source_folder,
                drafted_flag,
                draft.batch_size,
            )

            for summary in candidates:
                uid = summary.message_id
                parsed = await client.fetch_message(uid, folder=draft.source_folder)
                await displayer.display_thought(f"Drafting a reply to: {parsed.subject}")

                messages = [
                    ChatMessage(role=MessageRole.SYSTEM, content=draft.draft_prompt),
                    ChatMessage(
                        role=MessageRole.USER,
                        content=self._render_original(parsed.sender, parsed.subject, parsed.body_text),
                    ),
                ]
                async with llm_config.cost_reporting_llm(displayer) as llm:
                    llm_event = await displayer.display_llm_stream(llm_config, llm, messages, as_stop_step=False)
                draft_body = llm_event.chat_messages[-1].content or ""

                raw_draft = ReplyComposer.compose_from_parsed(
                    parsed, from_address=imap_config.username, body=draft_body
                )
                resolved_folder, draft_uid = await client.append_draft(draft.drafts_folder, raw_draft)
                await client.mark_drafted(draft.source_folder, uid, drafted_flag)
                logger.info(
                    "[imap] draft_batch_step: drafted uid=%s -> %r (draft_uid=%s), marked with %s",
                    uid,
                    resolved_folder,
                    draft_uid,
                    drafted_flag,
                )
                drafted.append(
                    DraftedReplyRef(
                        source_uid=uid,
                        drafts_folder=resolved_folder,
                        draft_uid=draft_uid,
                        in_reply_to=parsed.rfc_message_id,
                        subject=ReplyComposer.reply_subject(parsed.subject),
                        recipient=parsed.reply_to or parsed.sender,
                    )
                )

        return MailBatchDraftedEvent(source_folder=draft.source_folder, count=len(drafted), drafted=drafted)

    @step(
        name=AgentLocaleString(en="Finish drafting", de="Entwurf abschliessen"),
        icon="mage:check",
    )
    async def stop_drafts_step(self, _event: MailBatchDraftedEvent) -> StopEvent:
        """Terminate the drafting run once the batch has been drafted."""
        logger.info("[imap] stop_drafts_step: drafting run complete")
        return StopEvent()

    @staticmethod
    def _render_original(sender: str, subject: str, body_text: str | None) -> str:
        return f"From: {sender}\nSubject: {subject}\n\n{body_text or ''}"
