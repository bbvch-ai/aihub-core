"""Attached files and memory as tools: offered only when there is something to read, a model-chosen call runs the
capability's regular request, and its answer goes back to the loop as the tool's result."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.core.agents import AgentConfig
from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import (
    AttachedFilesReadEvent,
    MemoryRecalledEvent,
    ReadAttachedFilesEvent,
    RecallMemoryEvent,
    RunToolLoopEvent,
    ToolCallApprovedEvent,
    ToolCallsDecidedEvent,
    ToolLoopMode,
    ToolLoopState,
    ToolResultEvent,
    UserUploadedFile,
)
from swiss_ai_hub.core.generative_ai import CitationId
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.testing.auth_utils import fake_user

from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.agents.universal_agent.universal_agent import UniversalAgent
from swiss_ai_hub.agent.capabilities.attached_files.attached_files import AttachedFiles, answers_a_read_call
from swiss_ai_hub.agent.capabilities.memory.memory import Memory, answers_a_recall_call
from swiss_ai_hub.agent.capabilities.memory.memory_fields import MemoryFields
from swiss_ai_hub.agent.capabilities.memory.user_memory_config import UserMemoryConfig
from swiss_ai_hub.agent.capabilities.tool_loop.tool_context import ToolContext
from swiss_ai_hub.agent.capabilities.tool_loop.tool_loop_config import ToolLoopConfig
from swiss_ai_hub.agent.capabilities.tool_loop.tool_loop_fields import ToolLoopFields
from swiss_ai_hub.agent.i18n.agent_locale_handler import AgentLocaleHandler

T = AgentLocaleHandler("en")
F1 = "11111111-1111-4111-8111-111111111111"
F2 = "22222222-2222-4222-8222-222222222222"
F3 = "33333333-3333-4333-8333-333333333333"
REPORT = UserUploadedFile(filename="report.pdf", file_type="application/pdf", file_id=F1)
NOTES = UserUploadedFile(filename="notes.md", file_type="text/markdown", file_id=F2)
F4 = "44444444-4444-4444-8444-444444444444"
ORDERS = UserUploadedFile(
    filename="orders.xlsx", file_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", file_id=F4
)
PHOTO = UserUploadedFile(filename="photo.png", file_type="image/png", file_id=F3)


class _Config(MemoryFields, ToolLoopFields, AgentConfig):
    pass


def _config(**memory: Any) -> _Config:
    return _Config(
        agent_id="tools-test",
        name=LocaleString(en="Tools"),
        description=LocaleString(en="Tools fixture"),
        tool_loop=ToolLoopConfig(max_result_tokens=1_000),
        **memory,
    )


def _context(files: list[UserUploadedFile] | None = None, user: Any = None, **memory: Any) -> ToolContext:
    return ToolContext(
        agent_config=_config(**memory), displayer=MagicMock(spec=EventDisplayer), t=T, user=user, files=files or []
    )


def _decided(*tool_call_ids: str) -> ToolCallsDecidedEvent:
    state = ToolLoopState(messages=[], mode=ToolLoopMode.ANSWER)
    return ToolCallsDecidedEvent(state=state, tool_call_ids=list(tool_call_ids))


def _run_context(*features: str) -> MagicMock:
    run_context = MagicMock()
    run_context.get = AsyncMock(return_value=list(features))
    return run_context


def _call(name: str, **arguments: Any) -> ToolCallApprovedEvent:
    return ToolCallApprovedEvent(tool_call_id="c1", name=name, arguments=arguments, kind="capability")


class TestAttachedFilesAsATool:
    def test_the_attached_documents_are_listed_for_the_model(self):
        definition = AttachedFiles.tool_definition(_context([REPORT, PHOTO]))

        assert f"{CitationId.of(F1)}: report.pdf\n" in f"{definition.description}\n"
        assert F1 not in definition.description
        assert "photo.png" not in definition.description
        assert definition.parameters["properties"]["files"]["items"]["enum"] == [CitationId.of(F1)]

    def test_a_spreadsheet_is_marked_for_code_and_a_document_is_not(self):
        orders = UserUploadedFile(
            filename="orders.xlsx",
            file_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            file_id="33333333-3333-4333-8333-333333333333",
        )

        definition = AttachedFiles.tool_definition(_context([REPORT, orders]))

        hint = T("agent.attached_files.tool.structured_hint")
        listed = {
            line.split(": ", 1)[1].split(" ")[0]: line for line in definition.description.splitlines() if ": " in line
        }
        assert listed["orders.xlsx"].endswith(hint)
        assert hint not in listed["report.pdf"]

    def test_nothing_readable_attached_offers_no_tool(self):
        assert AttachedFiles.tool_definition(_context([PHOTO])) is None

    @pytest.mark.asyncio
    async def test_a_choice_naming_no_attached_file_is_refused_not_widened(self):
        conversation = MagicMock()
        conversation.input_budget.return_value = 10_000

        read = await AttachedFiles.read_tool_call_step(
            Agent(),
            call=_call("read_attached_files", files=["s000000"]),
            request=RunToolLoopEvent(files=[REPORT, NOTES, PHOTO]),
            conversation=conversation,
            loop=_config(),
            run_context=_run_context(),
            t=T,
        )

        assert isinstance(read, ToolResultEvent)
        assert read.is_error
        assert CitationId.of(F1) in read.content
        assert CitationId.of(F2) in read.content
        assert CitationId.of(F3) not in read.content

    @pytest.mark.asyncio
    async def test_a_choice_naming_only_an_image_is_refused_since_the_tool_never_offered_it(self):
        conversation = MagicMock()
        conversation.input_budget.return_value = 10_000

        read = await AttachedFiles.read_tool_call_step(
            Agent(),
            call=_call("read_attached_files", files=[CitationId.of(F3)]),
            request=RunToolLoopEvent(files=[REPORT, PHOTO]),
            conversation=conversation,
            loop=_config(),
            run_context=_run_context(),
            t=T,
        )

        assert isinstance(read, ToolResultEvent)
        assert read.is_error

    @pytest.mark.asyncio
    async def test_a_chosen_read_runs_the_regular_read_within_one_results_room(self):
        conversation = MagicMock()
        conversation.input_budget.return_value = 10_000

        read = await AttachedFiles.read_tool_call_step(
            Agent(),
            call=_call("read_attached_files", files=[CitationId.of(F2)], query="action items"),
            request=RunToolLoopEvent(files=[REPORT, NOTES]),
            conversation=conversation,
            loop=_config(),
            run_context=_run_context(),
            t=T,
        )

        assert isinstance(read, ReadAttachedFilesEvent)
        assert ([file.file_id for file in read.files], read.query, read.tool_call_id) == ([F2], "action items", "c1")
        assert read.reserve_tokens == 9_000

    @pytest.mark.asyncio
    async def test_with_code_on_a_chosen_spreadsheet_is_pointed_to_the_sandbox_not_read(self):
        conversation = MagicMock()
        conversation.input_budget.return_value = 10_000

        result = await AttachedFiles.read_tool_call_step(
            UniversalAgent(),
            call=_call("read_attached_files", files=[CitationId.of(F4)]),
            request=RunToolLoopEvent(files=[REPORT, ORDERS]),
            conversation=conversation,
            loop=_config(),
            run_context=_run_context("code_interpreter"),
            t=T,
        )

        assert isinstance(result, ToolResultEvent)
        assert not result.is_error
        assert "orders.xlsx" in result.content
        assert "run_command" in result.content

    @pytest.mark.asyncio
    async def test_with_code_on_a_mixed_choice_reads_the_document_and_keeps_the_spreadsheet(self):
        conversation = MagicMock()
        conversation.input_budget.return_value = 10_000

        read = await AttachedFiles.read_tool_call_step(
            UniversalAgent(),
            call=_call("read_attached_files", files=[CitationId.of(F1), CitationId.of(F4)]),
            request=RunToolLoopEvent(files=[REPORT, ORDERS]),
            conversation=conversation,
            loop=_config(),
            run_context=_run_context("code_interpreter"),
            t=T,
        )

        assert isinstance(read, ReadAttachedFilesEvent)
        assert [file.file_id for file in read.files] == [F1]
        assert [file.file_id for file in read.kept_for_code] == [F4]

    @pytest.mark.asyncio
    async def test_with_code_off_a_spreadsheet_is_read_like_any_file(self):
        conversation = MagicMock()
        conversation.input_budget.return_value = 10_000

        read = await AttachedFiles.read_tool_call_step(
            UniversalAgent(),
            call=_call("read_attached_files", files=[CitationId.of(F4)]),
            request=RunToolLoopEvent(files=[REPORT, ORDERS]),
            conversation=conversation,
            loop=_config(),
            run_context=_run_context(),
            t=T,
        )

        assert isinstance(read, ReadAttachedFilesEvent)
        assert [file.file_id for file in read.files] == [F4]
        assert read.kept_for_code == []

    @pytest.mark.asyncio
    async def test_what_was_read_goes_back_to_the_loop(self):
        block = [ChatMessage(role=MessageRole.SYSTEM, content="<REFERENCE_DOCUMENT id='s1'>Q1</REFERENCE_DOCUMENT>")]
        read = AttachedFilesReadEvent(block=block, tool_call_id="c1")

        assert await answers_a_read_call(read, _decided("c1"))
        result = await AttachedFiles.read_tool_result_step(Agent(), read=read, decided=_decided("c1"), t=T)

        assert isinstance(result, ToolResultEvent)
        assert (result.tool_call_id, result.block) == ("c1", block)
        assert "Q1" in result.content

    @pytest.mark.asyncio
    async def test_an_explicit_read_is_not_mistaken_for_a_tool_call(self):
        assert not await answers_a_read_call(AttachedFilesReadEvent(), _decided("c1"))


class TestMemoryAsATool:
    def test_offered_when_the_user_has_memory_to_read(self):
        assert Memory.tool_definition(_context(user=fake_user(), org_memory=None)) is not None

    def test_not_offered_without_a_scope_the_run_can_read(self):
        assert Memory.tool_definition(_context(user=None, org_memory=None)) is None
        no_retrieval = UserMemoryConfig(enable_user_memory_retrieval=False)
        assert Memory.tool_definition(_context(user=fake_user(), user_memory=no_retrieval, org_memory=None)) is None

    @pytest.mark.asyncio
    async def test_a_chosen_recall_runs_the_regular_recall(self):
        recall = await Memory.recall_tool_call_step(Agent(), call=_call("recall_memory", query="preferred language"))

        assert isinstance(recall, RecallMemoryEvent)
        assert (recall.query, recall.tool_call_id) == ("preferred language", "c1")

    @pytest.mark.asyncio
    async def test_what_memory_holds_goes_back_to_the_loop(self):
        recalled = MemoryRecalledEvent(
            user_block=[ChatMessage(role=MessageRole.SYSTEM, content="Prefers German.")], tool_call_id="c1"
        )

        assert await answers_a_recall_call(recalled, _decided("c1"))
        result = await Memory.recall_tool_result_step(Agent(), recalled=recalled, decided=_decided("c1"), t=T)

        assert "Prefers German." in result.content

    @pytest.mark.asyncio
    async def test_nothing_remembered_is_said_so(self):
        result = await Memory.recall_tool_result_step(
            Agent(), recalled=MemoryRecalledEvent(tool_call_id="c1"), decided=_decided("c1"), t=T
        )

        assert result.content == "Nothing is remembered for this."
