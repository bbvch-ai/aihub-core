import asyncio
from collections.abc import Sequence
from typing import ClassVar

from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.core.events.agent import (
    AttachedFileEvent,
    AttachedFilesReadEvent,
    AttachedFileStatus,
    ReadAttachedFilesEvent,
    UserUploadedFile,
)
from swiss_ai_hub.core.generative_ai import ExtractedDocument, estimate_prompt_tokens
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.topics import AgentInstanceTopic

from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.capabilities.attached_files.attached_file_reader import AttachedFileReader
from swiss_ai_hub.agent.capabilities.attached_files.attached_files_budget import AttachedFilesBudget
from swiss_ai_hub.agent.capabilities.capability import Capability
from swiss_ai_hub.agent.capabilities.conversation.conversation_fields import ConversationFields
from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString
from swiss_ai_hub.agent.workflow.decorators.step import step


class AttachedFiles(Capability):
    """
    The files the user attached to the conversation, as one call:

    - `read(files, history)` is answered with `AttachedFilesReadEvent`, one context block holding each file's full
      text, trimmed to fit next to `history`, empty when nothing readable is attached. Pass the block to
      `Conversation.compose(...)` behind the memories.

    Chat clients send every file of the current message branch on every turn, so a file attached earlier keeps
    answering later questions without being attached again, and an edited or regenerated message sees exactly its
    branch's files. The whole text goes in, rather than chunks a search would pick, because questions about a file
    ("summarise section 4") need all of it.
    """

    calls: ClassVar[dict] = {ReadAttachedFilesEvent: (AttachedFilesReadEvent,)}
    required_config: ClassVar[type[ConversationFields]] = ConversationFields

    ReadRequest = ReadAttachedFilesEvent
    Contents = AttachedFilesReadEvent

    @staticmethod
    def read(files: Sequence[UserUploadedFile] | None, history: list[ChatMessage]) -> ReadAttachedFilesEvent:
        return ReadAttachedFilesEvent(files=list(files or []), history=history)

    @staticmethod
    @step(
        name=AgentLocaleString.from_i18n_path("agent.attached_files.steps.read_attached_files.name"),
        description=AgentLocaleString.from_i18n_path("agent.attached_files.steps.read_attached_files.description"),
        icon="mdi:paperclip",
    )
    async def read_step(
        agent: Agent,
        request: ReadAttachedFilesEvent,
        topic: AgentInstanceTopic,
        conversation: ConversationFields,
        t: LocaleHandler,
    ) -> list[AttachedFileEvent | AttachedFilesReadEvent]:
        """Read every attached document, size the texts to the room left, and answer with them as one block."""
        files = [file for file in request.files if AttachedFileReader.is_readable_attachment(file)]
        if not files:
            return [AttachedFilesReadEvent()]

        outcomes = await asyncio.gather(
            *(AttachedFileReader.read(file, topic.agent_class, topic.agent_id) for file in files)
        )
        available = conversation.input_budget() - estimate_prompt_tokens(
            request.history, conversation.llm.token_counter
        )
        fitted = AttachedFilesBudget(available, conversation.llm.token_counter).fit(
            {event.file_id: document.content for document, event in outcomes if document is not None}
        )

        sections = [AttachedFiles._render(document, event, fitted, t) for document, event in outcomes]
        events = [AttachedFiles._with_status(event, fitted) for _, event in outcomes]
        block = [
            ChatMessage(
                role=MessageRole.SYSTEM,
                content="\n\n".join([t("agent.attached_files.prompt.preamble"), *sections]),
            )
        ]
        return [*events, AttachedFilesReadEvent(block=block)]

    @staticmethod
    def _render(
        document: ExtractedDocument | None,
        event: AttachedFileEvent,
        fitted: dict[str, tuple[str, bool]],
        t: LocaleHandler,
    ) -> str:
        if document is None:
            return t("agent.attached_files.prompt.unreadable", filename=event.filename, error=event.error)
        text, truncated = fitted[event.file_id]
        pages = f' pages="{event.number_of_pages}"' if event.number_of_pages else ""
        section = f'<attached_file name="{event.filename}"{pages}>\n{text}\n</attached_file>'
        if truncated:
            section += "\n" + t("agent.attached_files.prompt.truncated", filename=event.filename)
        return section

    @staticmethod
    def _with_status(event: AttachedFileEvent, fitted: dict[str, tuple[str, bool]]) -> AttachedFileEvent:
        if event.file_id in fitted and fitted[event.file_id][1]:
            return event.model_copy(update={"status": AttachedFileStatus.TRUNCATED})
        return event
