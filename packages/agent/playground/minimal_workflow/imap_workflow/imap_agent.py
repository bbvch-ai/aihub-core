from typing import ClassVar

from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import (
    MailFetchedEvent,
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
        en="Reads unread mail from an IMAP inbox and fetches a message with attachments",
        de="Liest ungelesene E-Mails aus einem IMAP-Posteingang und ruft eine Nachricht mit Anhängen ab",
        fr="Lit les e-mails non lus d'une boîte IMAP et récupère un message avec pièces jointes",
        it="Legge le e-mail non lette da una casella IMAP e recupera un messaggio con allegati",
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
            body_html=parsed.body_html,
            attachments=attachments,
        )

    @step(
        name=AgentLocaleString(en="Finish", de="Abschliessen"),
        icon="mage:check",
    )
    async def stop_step(self, _event: MailFetchedEvent) -> StopEvent:
        """Terminate the run once the chosen message has been fetched."""
        return StopEvent()
