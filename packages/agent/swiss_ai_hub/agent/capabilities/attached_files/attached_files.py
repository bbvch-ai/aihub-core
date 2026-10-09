import asyncio
import logging
from collections.abc import Sequence
from typing import ClassVar

from llama_index.core.base.llms.types import ChatMessage, MessageRole
from pydantic import ValidationError
from swiss_ai_hub.core.auth import UserIdentity
from swiss_ai_hub.core.events.agent import (
    AttachedFileEvent,
    AttachedFilesReadEvent,
    AttachedFileStatus,
    ChatFeature,
    ReadAttachedFilesEvent,
    RunToolLoopEvent,
    ToolCallApprovedEvent,
    ToolCallsDecidedEvent,
    ToolDefinition,
    ToolResultEvent,
    UserUploadedFile,
)
from swiss_ai_hub.core.generative_ai import (
    CitationId,
    ExtractedDocument,
    IngestedNode,
    combine_nodes_in_order,
    estimate_prompt_tokens,
)
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.topics import AgentInstanceTopic

from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.capabilities.attached_files.attached_file_fit_mode import FitMode
from swiss_ai_hub.agent.capabilities.attached_files.attached_file_page_range import AttachedFilePageRange
from swiss_ai_hub.agent.capabilities.attached_files.attached_file_reader import AttachedFileReader
from swiss_ai_hub.agent.capabilities.attached_files.attached_file_sections import AttachedFileSections
from swiss_ai_hub.agent.capabilities.attached_files.attached_files_budget import AttachedFilesBudget
from swiss_ai_hub.agent.capabilities.attached_files.attached_files_fields import AttachedFilesFields
from swiss_ai_hub.agent.capabilities.attached_files.attached_files_tool_arguments import AttachedFilesToolArguments
from swiss_ai_hub.agent.capabilities.capability import Capability
from swiss_ai_hub.agent.capabilities.conversation.conversation_fields import ConversationFields
from swiss_ai_hub.agent.capabilities.requested_features import RequestedFeatures
from swiss_ai_hub.agent.capabilities.structured_file import StructuredFile
from swiss_ai_hub.agent.capabilities.tool_loop.tool_context import ToolContext
from swiss_ai_hub.agent.capabilities.tool_loop.tool_loop_fields import ToolLoopFields
from swiss_ai_hub.agent.capabilities.tool_loop.tool_options import ToolOptions
from swiss_ai_hub.agent.context.run.run_context import RunContext
from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString
from swiss_ai_hub.agent.workflow.decorators.precondition import precondition
from swiss_ai_hub.agent.workflow.decorators.step import step

logger = logging.getLogger(__name__)

READ_ATTACHED_FILES_TOOL = "read_attached_files"


@precondition()
async def reads_attached_files(call: ToolCallApprovedEvent) -> bool:
    return call.name == READ_ATTACHED_FILES_TOOL


@precondition()
async def answers_a_read_call(read: AttachedFilesReadEvent, decided: ToolCallsDecidedEvent) -> bool:
    return read.tool_call_id is not None and read.tool_call_id in decided.tool_call_ids


class AttachedFiles(Capability):
    """
    The files the user attached to the conversation, as one call:

    - `read(files, history, query, reserve_tokens)` is answered with `AttachedFilesReadEvent`, one context block
      holding each file's text, empty when nothing readable is attached. `first_page`/`last_page` read those pages of
      a file that knows its pages, in order, instead of the sections closest to the query. Pass the block to
      `Conversation.compose(...)` behind the memories. `reserve_tokens` is room the caller still needs afterwards, such
      as RAG's retrieved knowledge, which the files leave free.

    Chat clients send every file of the current message branch on every turn, so a file attached earlier keeps
    answering later questions without being attached again, and an edited or regenerated message sees exactly its
    branch's files. A file that fits goes in whole, since questions about a file ("summarise section 4") need all of
    it; one that does not is cut down to the sections most relevant to the query.

    In a tool set, the model sees which files are attached and reads the ones it needs when it needs them, through
    the same read, within the room the loop leaves for one tool result.
    """

    calls: ClassVar[dict] = {ReadAttachedFilesEvent: (AttachedFilesReadEvent,)}
    required_config: ClassVar[type[AttachedFilesFields]] = AttachedFilesFields

    ReadRequest = ReadAttachedFilesEvent
    Contents = AttachedFilesReadEvent

    tool_name: ClassVar[str] = READ_ATTACHED_FILES_TOOL
    tool_options: ClassVar[ToolOptions] = ToolOptions(
        label=AgentLocaleString.from_i18n_path("agent.attached_files.tool.label"),
        approval_summary=AgentLocaleString.from_i18n_path("agent.attached_files.tool.approval_summary"),
    )

    @classmethod
    def tool_definition(cls, context: ToolContext) -> ToolDefinition | None:
        """Offered when the message carries a readable file; the description lists them, so the model knows they
        exist without their text taking room in every turn."""
        files = [file for file in context.files if AttachedFileReader.is_readable_attachment(file)]
        if not files:
            return None
        t = context.t
        # Files go by their citation id: a model shown the upload id cites that instead, which no client links.
        listing = "\n".join(
            f"- {CitationId.of(file.file_id)}: {file.filename}"
            + (
                f" {t('agent.attached_files.tool.structured_hint')}"
                if StructuredFile.works_better_in_code(file.filename)
                else ""
            )
            for file in files
        )
        return ToolDefinition(
            name=READ_ATTACHED_FILES_TOOL,
            description=t("agent.attached_files.tool.description", files=listing),
            parameters=AttachedFilesToolArguments.schema_for([CitationId.of(file.file_id) for file in files], t),
        )

    @staticmethod
    def _kept_for_code(files: Sequence[UserUploadedFile], t: LocaleHandler) -> str:
        return "\n".join(t("agent.attached_files.prompt.kept_for_code", filename=file.filename) for file in files)

    @staticmethod
    def read(
        files: Sequence[UserUploadedFile] | None,
        history: list[ChatMessage],
        query: str = "",
        reserve_tokens: int = 0,
        cite_sources: bool = True,
        first_page: int | None = None,
        last_page: int | None = None,
    ) -> ReadAttachedFilesEvent:
        return ReadAttachedFilesEvent(
            files=list(files or []),
            history=history,
            query=query,
            reserve_tokens=max(reserve_tokens, 0),
            cite_sources=cite_sources,
            first_page=first_page,
            last_page=last_page,
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
            return [AttachedFilesReadEvent(tool_call_id=request.tool_call_id)]

        outcomes = await AttachedFileReader.read_all(files, topic.agent_class, topic.agent_id)
        readable = {event.file_id: (document, event) for document, event in outcomes if document is not None}
        pages = AttachedFilePageRange.of(request.first_page, request.last_page)
        by_page = {file_id for file_id, (document, _) in readable.items() if pages and document.is_paged}
        sections = AttachedFiles._on_pages(await AttachedFiles._parse(readable), pages, by_page)
        counter = conversation.llm.token_counter
        available = (
            conversation.input_budget() - estimate_prompt_tokens(request.history, counter) - request.reserve_tokens
        )
        budget = AttachedFilesBudget(available, files_config.attached_files.share_of_input_budget, counter)
        rooms = budget.allocate(
            {file_id: "\n\n".join(section.content for section in found) for file_id, found in sections.items()}
        )
        picker = AttachedFileSections(files_config.attached_files, counter, user)
        fitted = await AttachedFiles._fit(sections, rooms, picker, request.query, by_page)

        events = [AttachedFiles._with_status(event, fitted) for _, event in outcomes]
        block = AttachedFiles._block(outcomes, fitted, t, request.cite_sources, pages)
        if request.kept_for_code:
            block.append(
                ChatMessage(role=MessageRole.SYSTEM, content=AttachedFiles._kept_for_code(request.kept_for_code, t))
            )
        return [*events, AttachedFilesReadEvent(block=block, tool_call_id=request.tool_call_id)]

    @staticmethod
    @step(
        name=AgentLocaleString.from_i18n_path("agent.attached_files.steps.read_as_tool.name"),
        description=AgentLocaleString.from_i18n_path("agent.attached_files.steps.read_as_tool.description"),
        icon="mdi:paperclip",
        precondition=reads_attached_files,
    )
    async def read_tool_call_step(
        agent: Agent,
        call: ToolCallApprovedEvent,
        request: RunToolLoopEvent,
        conversation: ConversationFields,
        loop: ToolLoopFields,
        run_context: RunContext,
        t: LocaleHandler,
    ) -> ReadAttachedFilesEvent | ToolResultEvent:
        """The model chose to read: the regular read of the files it picked, sized to one tool result's room.

        A choice naming no readable attached file is refused rather than widened to every file, which the model did
        not ask for; the refusal lists only the files the tool offered. While the code sandbox is offered, a chosen
        spreadsheet, presentation or CSV file is not read but named back to the model with where code finds it,
        since its Markdown text loses the structure and, for a large file, all but a slice."""
        try:
            arguments = AttachedFilesToolArguments.model_validate(call.arguments)
        except ValidationError as error:
            return ToolResultEvent(
                tool_call_id=call.tool_call_id, name=call.name, content=f"Invalid arguments: {error}", is_error=True
            )
        readable = [file for file in request.files if AttachedFileReader.is_readable_attachment(file)]
        chosen = [file for file in readable if not arguments.files or CitationId.of(file.file_id) in arguments.files]
        if not chosen:
            known = ", ".join(f"{CitationId.of(file.file_id)} ({file.filename})" for file in readable)
            return ToolResultEvent(
                tool_call_id=call.tool_call_id,
                name=call.name,
                content=t("agent.attached_files.tool.unknown_files", files=known),
                is_error=True,
            )
        code_runs = not loop.tool_loop.is_disabled("run_command") and await RequestedFeatures.contains(
            ChatFeature.CODE_INTERPRETER, run_context, type(agent)
        )
        kept = [file for file in chosen if code_runs and StructuredFile.works_better_in_code(file.filename)]
        if kept and len(kept) == len(chosen):
            return ToolResultEvent(
                tool_call_id=call.tool_call_id, name=call.name, content=AttachedFiles._kept_for_code(kept, t)
            )
        return ReadAttachedFilesEvent(
            files=[file for file in chosen if file not in kept],
            kept_for_code=kept,
            query=arguments.query,
            first_page=arguments.first_page,
            last_page=arguments.last_page,
            reserve_tokens=max(conversation.input_budget() - loop.tool_loop.max_result_tokens, 0),
            cite_sources=call.cite_sources,
            tool_call_id=call.tool_call_id,
        )

    @staticmethod
    @step(
        name=AgentLocaleString.from_i18n_path("agent.attached_files.steps.answer_tool_call.name"),
        description=AgentLocaleString.from_i18n_path("agent.attached_files.steps.answer_tool_call.description"),
        icon="mdi:paperclip",
        precondition=answers_a_read_call,
    )
    async def read_tool_result_step(
        agent: Agent, read: AttachedFilesReadEvent, decided: ToolCallsDecidedEvent, t: LocaleHandler
    ) -> ToolResultEvent:
        """Hand what was read back to the loop: its text for the model, its block for a gathered answer."""
        content = "\n\n".join(message.content for message in read.block if message.content)
        return ToolResultEvent(
            tool_call_id=read.tool_call_id,
            name=READ_ATTACHED_FILES_TOOL,
            content=content or t("agent.attached_files.tool.nothing_readable"),
            block=read.block,
        )

    @staticmethod
    async def _parse(
        readable: dict[str, tuple[ExtractedDocument, AttachedFileEvent]],
    ) -> dict[str, list[IngestedNode]]:
        parsed = await asyncio.gather(
            *(
                asyncio.to_thread(AttachedFileSections.parse, document, event.file_id, event.filename)
                for document, event in readable.values()
            )
        )
        return dict(zip(readable, parsed, strict=True))

    @staticmethod
    def _on_pages(
        sections: dict[str, list[IngestedNode]], pages: AttachedFilePageRange | None, by_page: set[str]
    ) -> dict[str, list[IngestedNode]]:
        """The sections on the pages asked for, of each file that knows its pages; a file that does not keeps all."""
        if pages is None:
            return sections
        return {file_id: pages.select(found) if file_id in by_page else found for file_id, found in sections.items()}

    @staticmethod
    async def _fit(
        sections: dict[str, list[IngestedNode]],
        rooms: dict[str, int | None],
        picker: AttachedFileSections,
        query: str,
        by_page: set[str],
    ) -> dict[str, tuple[list[IngestedNode], FitMode]]:
        """Pages asked for are kept in order up to the room, since they are read through, not searched."""

        async def fit_one(file_id: str) -> tuple[str, tuple[list[IngestedNode], FitMode]]:
            room = rooms[file_id]
            if file_id in by_page:
                if room is None:
                    return file_id, (sections[file_id], FitMode.PAGES)
                return file_id, (picker.fill_leading(sections[file_id], room), FitMode.PAGES_CUT)
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
        pages: AttachedFilePageRange | None = None,
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
        notes = [AttachedFiles._note(event, fitted, t, pages) for _, event in outcomes]
        if any(notes):
            block.append(ChatMessage(role=MessageRole.SYSTEM, content="\n".join(note for note in notes if note)))
        return block

    @staticmethod
    def _note(
        event: AttachedFileEvent,
        fitted: dict[str, tuple[list[IngestedNode], FitMode]],
        t: LocaleHandler,
        pages: AttachedFilePageRange | None = None,
    ) -> str:
        if event.file_id not in fitted:
            return t("agent.attached_files.prompt.unreadable", filename=event.filename, error=event.error)
        sections, mode = fitted[event.file_id]
        if mode in (FitMode.PAGES, FitMode.PAGES_CUT) and pages:
            return AttachedFiles._pages_note(event, sections, mode, pages, t)
        unknown_pages = t("agent.attached_files.prompt.pages_unknown", filename=event.filename) if pages else ""
        match mode:
            case FitMode.EXCERPTS:
                fit = t("agent.attached_files.prompt.excerpted", filename=event.filename)
            case FitMode.BEGINNING:
                fit = t("agent.attached_files.prompt.truncated", filename=event.filename)
            case _:
                fit = ""
        return "\n".join(note for note in (unknown_pages, fit) if note)

    @staticmethod
    def _pages_note(
        event: AttachedFileEvent,
        sections: list[IngestedNode],
        mode: FitMode,
        pages: AttachedFilePageRange,
        t: LocaleHandler,
    ) -> str:
        total = event.number_of_pages
        if not sections and total is not None and pages.first > total:
            return t(
                "agent.attached_files.prompt.pages_missing", filename=event.filename, total=total, first=pages.first
            )
        shown = pages.within(total)
        if mode == FitMode.PAGES_CUT:
            last_shown = max((AttachedFilePageRange.page_of(section) for section in sections), default=shown.first)
            return t(
                "agent.attached_files.prompt.pages_cut",
                filename=event.filename,
                first=shown.first,
                shown=last_shown,
                last=shown.last,
                next=last_shown + 1,
            )
        return t(
            "agent.attached_files.prompt.pages",
            filename=event.filename,
            first=shown.first,
            last=shown.last,
            total=total or shown.last,
        )

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
