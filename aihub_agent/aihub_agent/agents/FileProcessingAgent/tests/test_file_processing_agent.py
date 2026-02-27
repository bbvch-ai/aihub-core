from unittest.mock import patch

import pytest
from aihub_lib.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthSettings import (
    DangerousDevelopmentOnlyAuthSettings,
)
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.logging.logger import enable_logging
from aihub_lib.nats.events import UserMessageEvent
from aihub_lib.nats.events.common.LimitChatHistoryEvent import LimitChatHistoryEvent
from aihub_lib.nats.events.user.UserUploadedFile import UserUploadedFile
from aihub_lib.nats.topics.agents.AgentInstanceTopic import AgentInstanceTopic
from aihub_lib.testing.asyncio_utils.bdd import async_test
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from pytest_bdd import given, parsers, scenarios, then, when

from aihub_agent.agents.FileProcessingAgent.FileProcessingAgent import FileProcessingAgent
from aihub_agent.agents.FileProcessingAgent.FileProcessingAgentConfig import FileProcessingAgentConfig
from aihub_agent.agents.FileProcessingAgent.events.FileContentEvent import FileContentEvent
from aihub_agent.runners.AgentTestRunner import AgentTestRunner

scenarios("features/file_processing_agent.feature")

enable_logging()


# ---------------------------------------------------------------------------
# BDD fixtures & steps (integration test — requires NATS + LLM)
# ---------------------------------------------------------------------------


@pytest.fixture
def self_hosted_llm_config():
    return LLMConfig(model_name="text-generation/gpt-oss-120b")


@given("a FileProcessingAgent runner with a valid self hosted configuration", target_fixture="agent_runner")
def _(self_hosted_llm_config):
    config = FileProcessingAgentConfig(
        agent_id="file_processing_agent",
        name=LocaleString(en="File Processing Agent"),
        description=LocaleString(en="Test file processing agent"),
        system_prompt=LocaleString(en="You are a helpful assistant."),
        number_of_input_tokens=100000,
        llm=self_hosted_llm_config,
    )
    return AgentTestRunner(agent_type=FileProcessingAgent, agent_config=config)


@when(parsers.parse('the start event is sent with a user query "{query}"'))
@async_test
async def _(agent_runner: AgentTestRunner, query: str):
    async with agent_runner.test_run(delay_before_stop=30) as topic:
        await agent_runner.send_event_from_topic(
            topic=topic,
            start_event=UserMessageEvent(
                locale="en",
                user=DangerousDevelopmentOnlyAuthSettings().get_user_identity(),
                messages=[ChatMessage(content=query, role=MessageRole.USER)],
            ),
        )


@then("a StartEvent is present")
def _(agent_runner: AgentTestRunner):
    assert agent_runner.has_start_event, "Agent did not receive StartEvent"


@then("a LimitChatHistoryEvent is present")
def _(agent_runner: AgentTestRunner):
    assert agent_runner.has_event_of_class(LimitChatHistoryEvent), "Agent did not produce a LimitChatHistoryEvent"


@then("a StopEvent is present")
def _(agent_runner: AgentTestRunner):
    assert agent_runner.has_stop_event, "Agent did not produce StopEvent"


# ---------------------------------------------------------------------------
# Unit tests — step logic (no infrastructure needed)
# ---------------------------------------------------------------------------


def _make_uploaded_file(filename: str = "test.txt", file_type: str = "text/plain") -> UserUploadedFile:
    return UserUploadedFile(filename=filename, file_type=file_type, file_id="00000000-0000-4000-a000-000000000001")


def _make_topic() -> AgentInstanceTopic:
    return AgentInstanceTopic(
        agent_class="FileProcessingAgent",
        agent_id="test-agent",
        thread_id="thread-1",
        display_id="display-1",
        run_id="run-1",
        event_type="control_event",
        event_name="test",
        event_id="evt-1",
    )


def _make_config() -> FileProcessingAgentConfig:
    return FileProcessingAgentConfig(
        agent_id="test",
        name=LocaleString(en="Test"),
        description=LocaleString(en="Test"),
        system_prompt=LocaleString(en="You are a helpful assistant."),
        number_of_input_tokens=100000,
        llm=LLMConfig(model_name="test-model"),
    )


def _make_user_message_event(
    query: str = "Summarize the file",
    files: list[UserUploadedFile] | None = None,
) -> UserMessageEvent:
    return UserMessageEvent(
        locale="en",
        user=DangerousDevelopmentOnlyAuthSettings().get_user_identity(),
        messages=[ChatMessage(content=query, role=MessageRole.USER)],
        files=files,
    )


class TestExtractFilesStep:
    """Test extract_files_step downloads files and produces FileContentEvent."""

    @patch("aihub_lib.generative_ai.document.download_and_format_files.download_user_file")
    @pytest.mark.asyncio
    async def test_single_text_file(self, mock_download):
        content = b"Hello, world!"
        mock_download.return_value = content
        uploaded = _make_uploaded_file("readme.txt")
        event = _make_user_message_event(files=[uploaded])

        agent = FileProcessingAgent()
        result = await agent.extract_files_step(event, _make_topic())

        assert isinstance(result, FileContentEvent)
        assert "readme.txt" in result.file_context
        assert "Hello, world!" in result.file_context
        assert f"{len(content)} bytes" in result.file_context

    @patch("aihub_lib.generative_ai.document.download_and_format_files.download_user_file")
    @pytest.mark.asyncio
    async def test_multiple_files(self, mock_download):
        mock_download.side_effect = [b"File A content", b"File B content"]
        files = [_make_uploaded_file("a.txt"), _make_uploaded_file("b.log")]
        event = _make_user_message_event(files=files)

        agent = FileProcessingAgent()
        result = await agent.extract_files_step(event, _make_topic())

        assert "a.txt" in result.file_context
        assert "File A content" in result.file_context
        assert "b.log" in result.file_context
        assert "File B content" in result.file_context

    @patch("aihub_lib.generative_ai.document.download_and_format_files.download_user_file")
    @pytest.mark.asyncio
    async def test_binary_file_decoded_with_replacement(self, mock_download):
        mock_download.return_value = b"\x89PNG\r\n\x1a\n"
        uploaded = _make_uploaded_file("image.png", "image/png")
        event = _make_user_message_event(files=[uploaded])

        agent = FileProcessingAgent()
        result = await agent.extract_files_step(event, _make_topic())

        assert "image.png" in result.file_context
        assert "8 bytes" in result.file_context


class TestPrepareMessagesStep:
    """Test that prepare_messages_step assembles chat history correctly."""

    @pytest.mark.asyncio
    async def test_file_content_prepended_to_user_message(self):
        event = _make_user_message_event(query="What errors do you see?")
        file_content = FileContentEvent(
            file_context="--- errors.log (37 bytes) ---\nError log line 1\nError log line 2"
        )

        agent = FileProcessingAgent()
        result = await agent.prepare_messages_step(event, file_content, _make_config())

        assert isinstance(result, LimitChatHistoryEvent)
        user_messages = [m for m in result.limited_history if m.role == MessageRole.USER]
        last_user_content = user_messages[-1].content
        assert "Error log line 1" in last_user_content
        assert "What errors do you see?" in last_user_content

    @pytest.mark.asyncio
    async def test_no_files_passes_through_unchanged(self):
        event = _make_user_message_event(query="Hello")

        agent = FileProcessingAgent()
        result = await agent.prepare_messages_step(event, None, _make_config())

        assert isinstance(result, LimitChatHistoryEvent)
        user_messages = [m for m in result.limited_history if m.role == MessageRole.USER]
        assert user_messages[-1].content == "Hello"
