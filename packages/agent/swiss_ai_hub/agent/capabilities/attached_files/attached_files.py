import asyncio
import html
import logging
from collections.abc import Sequence
from typing import ClassVar

from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.core.auth import UserIdentity
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
from swiss_ai_hub.agent.capabilities.attached_files.attached_file_fit_mode import FitMode
from swiss_ai_hub.agent.capabilities.attached_files.attached_file_reader import AttachedFileReader
from swiss_ai_hub.agent.capabilities.attached_files.attached_file_section_selector import AttachedFileSectionSelector
from swiss_ai_hub.agent.capabilities.attached_files.attached_files_budget import AttachedFilesBudget
from swiss_ai_hub.agent.capabilities.attached_files.attached_files_fields import AttachedFilesFields
from swiss_ai_hub.agent.capabilities.capability import Capability
from swiss_ai_hub.agent.capabilities.conversation.conversation_fields import ConversationFields
from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString
from swiss_ai_hub.agent.workflow.decorators.step import step

logger = logging.getLogger(__name__)


class AttachedFiles(Capability):
    """
    The files the user attached to the conversation, as one call:

    - `read(files, history, query, reserve_tokens)` is answered with `AttachedFilesReadEvent`, one context block
      holding each file's text, empty when nothing readable is attached. Pass the block to `Conversation.compose(...)`
      behind the memories. `reserve_tokens` is room the caller still needs afterwards, such as RAG's retrieved
      knowledge, which the files leave free.

    Chat clients send every file of the current message branch on every turn, so a file attached earlier keeps
    answering later questions without being attached again, and an edited or regenerated message sees exactly its
    branch's files. A file that fits goes in whole, since questions about a file ("summarise section 4") need all of
    it; one that does not is cut down to the sections most relevant to the query.
    """

    calls: ClassVar[dict] = {ReadAttachedFilesEvent: (AttachedFilesReadEvent,)}
    required_config: ClassVar[type[AttachedFilesFields]] = AttachedFilesFields

    ReadRequest = ReadAttachedFilesEvent
    Contents = AttachedFilesReadEvent

    @staticmethod
    def read(
        files: Sequence[UserUploadedFile] | None,
        history: list[ChatMessage],
        query: str = "",
        reserve_tokens: int = 0,
    ) -> ReadAttachedFilesEvent:
        return ReadAttachedFilesEvent(
            files=list(files or []), history=history, query=query, reserve_tokens=max(reserve_tokens, 0)
        )

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
        files_config: AttachedFilesFields,
        t: LocaleHandler,
        user: UserIdentity | None = None,
    ) -> list[AttachedFileEvent | AttachedFilesReadEvent]:
        """Read every attached document, size the texts to the room left, and answer with them as one block."""
        files = [file for file in request.files if AttachedFileReader.is_readable_attachment(file)]
        if not files:
            return [AttachedFilesReadEvent()]

        outcomes = await asyncio.gather(
            *(AttachedFileReader.read(file, topic.agent_class, topic.agent_id) for file in files)
        )
        counter = conversation.llm.token_counter
        available = (
            conversation.input_budget() - estimate_prompt_tokens(request.history, counter) - request.reserve_tokens
        )
        budget = AttachedFilesBudget(available, counter)
        texts = {event.file_id: document.content for document, event in outcomes if document is not None}
        selector = AttachedFileSectionSelector(files_config.attached_files, counter, user)
        fitted = await AttachedFiles._fit(texts, budget.allocate(texts), budget, selector, request.query)

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
    async def _fit(
        texts: dict[str, str],
        rooms: dict[str, int | None],
        budget: AttachedFilesBudget,
        selector: AttachedFileSectionSelector,
        query: str,
    ) -> dict[str, tuple[str, FitMode]]:
        async def fit_one(file_id: str) -> tuple[str, tuple[str, FitMode]]:
            room = rooms[file_id]
            if room is None:
                return file_id, (texts[file_id], FitMode.WHOLE)
            return file_id, await AttachedFiles._cut_down(texts[file_id], room, budget, selector, query)

        return dict(await asyncio.gather(*(fit_one(file_id) for file_id in texts)))

    @staticmethod
    async def _cut_down(
        text: str, room: int, budget: AttachedFilesBudget, selector: AttachedFileSectionSelector, query: str
    ) -> tuple[str, FitMode]:
        """Relevant sections when the models can pick them; the beginning otherwise.

        The fallback keeps the turn answering when the embedding or reranking service is down or the turn has no
        query to rank against, rather than losing the file.
        """
        if query.strip():
            try:
                return await selector.select(text, query, room), FitMode.EXCERPTS
            except Exception:
                logger.exception("[attached-files] Could not pick relevant sections, keeping the beginning instead")
        return budget.trim_head(text, room), FitMode.BEGINNING

    @staticmethod
    def _render(
        document: ExtractedDocument | None,
        event: AttachedFileEvent,
        fitted: dict[str, tuple[str, FitMode]],
        t: LocaleHandler,
    ) -> str:
        if document is None:
            return t("agent.attached_files.prompt.unreadable", filename=event.filename, error=event.error)
        text, mode = fitted[event.file_id]
        pages = f' pages="{event.number_of_pages}"' if event.number_of_pages else ""
        section = f'<attached_file name="{html.escape(event.filename, quote=True)}"{pages}>\n{text}\n</attached_file>'
        if mode == FitMode.EXCERPTS:
            section += "\n" + t("agent.attached_files.prompt.excerpted", filename=event.filename)
        elif mode == FitMode.BEGINNING:
            section += "\n" + t("agent.attached_files.prompt.truncated", filename=event.filename)
        return section

    @staticmethod
    def _with_status(event: AttachedFileEvent, fitted: dict[str, tuple[str, FitMode]]) -> AttachedFileEvent:
        if event.file_id in fitted and fitted[event.file_id][1] != FitMode.WHOLE:
            return event.model_copy(update={"status": AttachedFileStatus.TRUNCATED})
        return event
