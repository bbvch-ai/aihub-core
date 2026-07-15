from typing import ClassVar

from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import (
    MailFetchedEvent,
    MailMovedEvent,
    StopEvent,
    UnreadMailListedEvent,
)
from swiss_ai_hub.core.imap import ImapClientConfig
from swiss_ai_hub.core.topics import AgentInstanceTopic

from playground.minimal_workflow.imap_workflow.events.read_mail_start_event import ReadMailStartEvent
from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString
from swiss_ai_hub.agent.imap.imap_client import ImapClientFactory
from swiss_ai_hub.agent.imap.mail_attachment_store import MailAttachmentStore
from swiss_ai_hub.agent.workflow.decorators.step import step


class ImapAgent(Agent):
    """Demonstrator for the IMAP read capability — lists unread mail, then fetches one message with attachments.

    Non-conversational (like RetrievalAgent): triggered by ReadMailStartEvent, configured via its form, and used as a
    reference/building block — it is not exposed in the chat UI.
    """

    name: ClassVar[AgentLocaleString] = AgentLocaleString(
        en="IMAP Agent", de="IMAP-Agent", fr="Agent IMAP", it="Agente IMAP"
    )
    description: ClassVar[AgentLocaleString] = AgentLocaleString(
        en="Reads unread mail from an IMAP inbox, fetches a message with attachments, and optionally files it away",
        de="Liest ungelesene E-Mails aus einem IMAP-Posteingang, ruft eine Nachricht mit Anhängen ab und legt sie "
        "optional ab",
        fr="Lit les e-mails non lus d'une boîte IMAP, récupère un message avec pièces jointes et le classe "
        "éventuellement",
        it="Legge le e-mail non lette da una casella IMAP, recupera un messaggio con allegati e lo archivia "
        "facoltativamente",
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
        async with ImapClientFactory.create(imap_config) as client:
            summaries = await client.list_unread()
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
            await displayer.display_thought("No unread messages in the inbox.")
            return StopEvent()

        message_id = event.messages[0].message_id
        async with ImapClientFactory.create(imap_config) as client:
            parsed = await client.fetch_message(message_id)

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
        """File the fetched message into the processed folder; skip when moving is disabled in the config."""
        if not imap_config.enable_move:
            await displayer.display_thought("Moving is disabled — leaving the message in the inbox.")
            return StopEvent()
        if not imap_config.processed_folder:
            raise ValueError("enable_move is on but processed_folder is empty")

        async with ImapClientFactory.create(imap_config) as client:
            await client.move_message(event.message_id, imap_config.processed_folder)
        return MailMovedEvent(
            message_id=event.message_id,
            source_folder=imap_config.inbox_folder,
            target_folder=imap_config.processed_folder,
        )

    @step(
        name=AgentLocaleString(en="Finish", de="Abschliessen"),
        icon="mage:check",
    )
    async def stop_step(self, _event: MailMovedEvent) -> StopEvent:
        """Terminate the run once the chosen message has been moved."""
        return StopEvent()
