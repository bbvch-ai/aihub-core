import asyncio
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
from swiss_ai_hub.core.generative_ai import (
    ExtractedDocument,
    IngestedNode,
    combine_nodes_in_order,
    estimate_prompt_tokens,
)
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.topics import AgentInstanceTopic

from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.capabilities.attached_files.attached_file_fit_mode import FitMode
from swiss_ai_hub.agent.capabilities.attached_files.attached_file_reader import AttachedFileReader
from swiss_ai_hub.agent.capabilities.attached_files.attached_file_sections import AttachedFileSections
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
        cite_sources: bool = True,
    ) -> ReadAttachedFilesEvent:
        return ReadAttachedFilesEvent(
            files=list(files or []),
            history=history,
            query=query,
            reserve_tokens=max(reserve_tokens, 0),
            cite_sources=cite_sources,
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
        readable = {event.file_id: (document, event) for document, event in outcomes if document is not None}
        sections = dict(
            zip(
                readable,
                await asyncio.gather(
                    *(
                        asyncio.to_thread(AttachedFileSections.parse, document, event.file_id, event.filename)
                        for document, event in readable.values()
                    )
                ),
                strict=True,
            )
        )
        counter = conversation.llm.token_counter
        available = (
            conversation.input_budget() - estimate_prompt_tokens(request.history, counter) - request.reserve_tokens
        )
        budget = AttachedFilesBudget(available, files_config.attached_files.share_of_input_budget, counter)
        rooms = budget.allocate({file_id: document.content for file_id, (document, _) in readable.items()})
        picker = AttachedFileSections(files_config.attached_files, counter, user)
        fitted = await AttachedFiles._fit(sections, rooms, picker, request.query)

        events = [AttachedFiles._with_status(event, fitted) for _, event in outcomes]
        block = AttachedFiles._block(outcomes, fitted, t, request.cite_sources)
        return [*events, AttachedFilesReadEvent(block=block)]

    @staticmethod
    async def _fit(
        sections: dict[str, list[IngestedNode]],
        rooms: dict[str, int | None],
        picker: AttachedFileSections,
        query: str,
    ) -> dict[str, tuple[list[IngestedNode], FitMode]]:
        async def fit_one(file_id: str) -> tuple[str, tuple[list[IngestedNode], FitMode]]:
            room = rooms[file_id]
            if room is None:
                return file_id, (sections[file_id], FitMode.WHOLE)
            return file_id, await AttachedFiles._cut_down(sections[file_id], room, picker, query)

        return dict(await asyncio.gather(*(fit_one(file_id) for file_id in sections)))

    @staticmethod
    async def _cut_down(
        sections: list[IngestedNode], room: int, picker: AttachedFileSections, query: str
    ) -> tuple[list[IngestedNode], FitMode]:
        """Relevant sections when the models can pick them; the beginning otherwise.

        The fallback keeps the turn answering when the embedding or reranking service is down or the turn has no
        query to rank against, rather than losing the file.
        """
        if query.strip():
            try:
                return picker.fill(await picker.rank(sections, query), room), FitMode.EXCERPTS
            except Exception:
                logger.exception("[attached-files] Could not pick relevant sections, keeping the beginning instead")
        return picker.fill(sections, room), FitMode.BEGINNING

    @staticmethod
    def _block(
        outcomes: Sequence[tuple[ExtractedDocument | None, AttachedFileEvent]],
        fitted: dict[str, tuple[list[IngestedNode], FitMode]],
        t: LocaleHandler,
        cite_sources: bool,
    ) -> list[ChatMessage]:
        """The files as retrieved knowledge is rendered, followed by what the model must tell the user about them."""
        chosen = [section for sections, _ in fitted.values() for section in sections]
        block = []
        if chosen:
            block.append(
                combine_nodes_in_order(
                    chosen, t, AgentLocaleString.from_i18n_path("agent.attached_files.prompt.context")
                )
            )
            if cite_sources:
                block.append(ChatMessage(role=MessageRole.SYSTEM, content=t("lib.prompt.citations.instruction")))
        notes = [AttachedFiles._note(event, fitted, t) for _, event in outcomes]
        if any(notes):
            block.append(ChatMessage(role=MessageRole.SYSTEM, content="\n".join(note for note in notes if note)))
        return block

    @staticmethod
    def _note(event: AttachedFileEvent, fitted: dict[str, tuple[list[IngestedNode], FitMode]], t: LocaleHandler) -> str:
        if event.file_id not in fitted:
            return t("agent.attached_files.prompt.unreadable", filename=event.filename, error=event.error)
        match fitted[event.file_id][1]:
            case FitMode.EXCERPTS:
                return t("agent.attached_files.prompt.excerpted", filename=event.filename)
            case FitMode.BEGINNING:
                return t("agent.attached_files.prompt.truncated", filename=event.filename)
        return ""

    @staticmethod
    def _with_status(
        event: AttachedFileEvent, fitted: dict[str, tuple[list[IngestedNode], FitMode]]
    ) -> AttachedFileEvent:
        """The text the model received, and whether it was all of the file."""
        if event.file_id not in fitted:
            return event
        sections, mode = fitted[event.file_id]
        status = AttachedFileStatus.READ if mode == FitMode.WHOLE else AttachedFileStatus.TRUNCATED
        return event.model_copy(
            update={"status": status, "content": "\n\n".join(section.content for section in sections)}
        )
