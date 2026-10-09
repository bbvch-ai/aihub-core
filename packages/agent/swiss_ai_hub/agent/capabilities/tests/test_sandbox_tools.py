"""How agents work in the user's code sandbox: in a folder per conversation that holds its attached files, and with
every file shown to the user copied into our storage so the answer keeps it."""

import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from swiss_ai_hub.core.agents import AgentConfig
from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import ChatFeature, SandboxFileDisplayedEvent, UserUploadedFile
from swiss_ai_hub.core.generative_ai import ExtractedDocument
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.infrastructure import ConversationAttachments, OpenTerminalError
from swiss_ai_hub.core.testing.auth_utils import fake_user
from swiss_ai_hub.core.topics import AgentInstanceTopic

from swiss_ai_hub.agent.agents.universal_agent.universal_agent import UniversalAgent
from swiss_ai_hub.agent.capabilities.sandbox import sandbox_workspace
from swiss_ai_hub.agent.capabilities.sandbox.sandbox_tools import SandboxTools
from swiss_ai_hub.agent.capabilities.sandbox.sandbox_workspace import SandboxWorkspace
from swiss_ai_hub.agent.capabilities.sandbox.user_files_tools import UserFilesTools
from swiss_ai_hub.agent.capabilities.tool_loop.tool_context import ToolContext
from swiss_ai_hub.agent.capabilities.tool_loop.tool_set import ToolSet
from swiss_ai_hub.agent.i18n.agent_locale_handler import AgentLocaleHandler

THREAD = "65f1c0ffee00000000000001"
USER_FILE_PAGES = "swiss_ai_hub.agent.capabilities.sandbox.user_file_pages"
REPORT = UserUploadedFile(filename="sales.csv", file_type="text/csv", file_id="0f8fad5b-d9cb-469f-a165-70867728950e")


def _topic() -> AgentInstanceTopic:
    return AgentInstanceTopic(
        agent_class="UniversalAgent",
        agent_id="assistant",
        thread_id=THREAD,
        display_id="65f1c0ffee00000000000002",
        run_id="65f1c0ffee00000000000003",
        event_type="control_event",
        event_name="ToolCallApprovedEvent",
        event_id="65f1c0ffee00000000000004",
    )


def _extracted(content: str, pages: int) -> ExtractedDocument:
    return ExtractedDocument(
        title="Report",
        content=content,
        content_type="application/pdf",
        source_filename="q1.pdf",
        document_parser="MineruLoader",
        number_of_pages=pages,
    )


def _client(present: list[str] | None = None, staged: dict[str, str] | None = None) -> MagicMock:
    async def view(path: str) -> tuple[bytes, str]:
        if not path.endswith(ConversationAttachments.RECORD):
            return b"\x89PNG", "image/png"
        if staged is None:
            raise OpenTerminalError("404: File not found", 404)
        return json.dumps(staged).encode(), "application/json"

    client = MagicMock()
    client.list_files = AsyncMock(return_value={"entries": [{"name": name} for name in present or []]})
    client.upload = AsyncMock(return_value={})
    client.write_file = AsyncMock(return_value={})
    client.mkdir = AsyncMock(return_value={})
    client.execute = AsyncMock(return_value={"status": "done", "exit_code": 0, "output": [{"data": "42\r\n"}]})
    client.view = AsyncMock(side_effect=view)
    return client


def _context(files: list[UserUploadedFile] | None = None) -> ToolContext:
    displayer = MagicMock(spec=EventDisplayer)
    displayer.display_event = AsyncMock()
    return ToolContext(
        agent_config=AgentConfig(
            agent_id="sandbox-test", name=LocaleString(en="Sandbox"), description=LocaleString(en="Sandbox fixture")
        ),
        displayer=displayer,
        t=AgentLocaleHandler("en"),
        user=fake_user(),
        files=files or [],
        topic=_topic(),
    )


@pytest.fixture
def s3() -> Any:
    with patch.object(sandbox_workspace, "create_s3_client") as create:
        create.return_value.get_object.return_value = {"Body": MagicMock(read=MagicMock(return_value=b"a,b\n1,2"))}
        yield create.return_value


@pytest.fixture
def sandbox() -> Any:
    client = _client()
    with (
        patch.object(sandbox_workspace.OpenWebuiAccountEntity, "openwebui_id_of", return_value="owui-1"),
        patch.object(sandbox_workspace, "OpenTerminalClient", return_value=client) as created,
    ):
        client.created = created
        yield client


class TestPaths:
    workspace = SandboxWorkspace(_client(), _topic(), [])

    def test_a_relative_path_lies_in_the_conversation_folder(self) -> None:
        assert self.workspace.path("out/chart.png") == f"conversations/{THREAD}/out/chart.png"

    def test_a_tilde_path_lies_in_the_home(self) -> None:
        assert self.workspace.path("~/notes.txt") == "notes.txt"
        assert self.workspace.path("~") == "."

    @pytest.mark.parametrize("path", ["/etc/passwd", "/proc/1/environ", "../../../etc", "~/../other", "a\0b"])
    def test_a_path_outside_the_home_is_refused(self, path: str) -> None:
        with pytest.raises(OpenTerminalError):
            self.workspace.path(path)


class TestAttachedFiles:
    @pytest.mark.asyncio
    async def test_attached_files_are_placed_in_the_conversation_folder(self, s3: Any) -> None:
        client = _client()

        await SandboxWorkspace(client, _topic(), [REPORT]).prepare()

        s3.get_object.assert_called_once_with(
            Bucket="agent-files", Key=f"UniversalAgent/assistant/{REPORT.file_id}/sales.csv"
        )
        client.upload.assert_awaited_once_with(f"conversations/{THREAD}", "sales.csv", b"a,b\n1,2")
        client.write_file.assert_awaited_once_with(
            f"conversations/{THREAD}/.attached_files.json", json.dumps({REPORT.file_id: "sales.csv"})
        )

    @pytest.mark.asyncio
    async def test_a_staged_file_is_not_placed_again_even_after_the_code_deleted_it(self, s3: Any) -> None:
        client = _client(present=[], staged={REPORT.file_id: "sales.csv"})

        await SandboxWorkspace(client, _topic(), [REPORT]).prepare()

        client.upload.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_a_new_file_with_a_taken_name_is_placed_beside_the_first(self, s3: Any) -> None:
        newer = REPORT.model_copy(update={"file_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7"})
        client = _client(present=["sales.csv"], staged={REPORT.file_id: "sales.csv"})

        await SandboxWorkspace(client, _topic(), [REPORT, newer]).prepare()

        client.upload.assert_awaited_once_with(f"conversations/{THREAD}", "sales (2).csv", b"a,b\n1,2")

    @pytest.mark.asyncio
    async def test_two_files_with_one_name_on_one_message_both_stay(self, s3: Any) -> None:
        other = REPORT.model_copy(update={"file_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7"})
        client = _client()

        await SandboxWorkspace(client, _topic(), [REPORT, other]).prepare()

        assert [call.args[1] for call in client.upload.await_args_list] == ["sales.csv", "sales (2).csv"]

    @pytest.mark.asyncio
    async def test_a_message_without_files_only_creates_the_folder_commands_run_in(self) -> None:
        client = _client()

        await SandboxWorkspace(client, _topic(), []).prepare()

        client.mkdir.assert_awaited_once_with(f"conversations/{THREAD}")
        client.view.assert_not_awaited()
        client.list_files.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_a_new_conversation_starts_with_no_folder(self, s3: Any) -> None:
        client = _client()
        client.list_files = AsyncMock(side_effect=OpenTerminalError("404: Directory not found", 404))

        await SandboxWorkspace(client, _topic(), [REPORT]).prepare()

        client.upload.assert_awaited_once()


class TestTools:
    @pytest.mark.asyncio
    async def test_commands_run_as_the_user_in_the_conversation_folder(self, sandbox: Any) -> None:
        result = await SandboxTools(_context()).run_command("python3 -c 'print(6*7)'")

        sandbox.created.assert_called_once_with("owui-1")
        sandbox.execute.assert_awaited_once_with("python3 -c 'print(6*7)'", cwd=f"conversations/{THREAD}", wait=60)
        assert result == "Command finished successfully (exit code 0).\n42"

    @pytest.mark.asyncio
    async def test_a_spreadsheet_is_sent_to_code_instead_of_being_read_as_text(self, sandbox: Any) -> None:
        sandbox.read_file = AsyncMock()

        result = await SandboxTools(_context()).read_file("data/orders.xlsx")

        sandbox.read_file.assert_not_awaited()
        assert result.startswith("orders.xlsx is a spreadsheet or presentation")
        assert "run_command" in result

    @pytest.mark.asyncio
    async def test_a_failed_command_says_so_and_how_to_go_on(self, sandbox: Any) -> None:
        sandbox.execute = AsyncMock(return_value={"status": "done", "exit_code": 1, "output": [{"data": "KeyError"}]})

        result = await SandboxTools(_context()).run_command("python3 broken.py")

        assert result.startswith("Command failed (exit code 1). Read the error below and fix the command.")
        assert result.endswith("KeyError")

    @pytest.mark.asyncio
    async def test_the_files_a_command_made_or_changed_are_named_with_how_to_hand_them_over(self, sandbox: Any) -> None:
        before = {"entries": [{"name": "orders.xlsx", "type": "file", "size": 2_200_000, "modified": 1.0}]}
        after = {
            "entries": [
                {"name": "orders.xlsx", "type": "file", "size": 2_200_000, "modified": 1.0},
                {"name": "orders-net.xlsx", "type": "file", "size": 3_100_000, "modified": 2.0},
                {"name": ".attached_files.json", "type": "file", "size": 80, "modified": 2.0},
                {"name": "charts", "type": "directory", "modified": 2.0},
            ]
        }
        sandbox.list_files = AsyncMock(side_effect=[before, after])

        result = await SandboxTools(_context()).run_command("python3 net.py")

        assert result.endswith(
            "Files created or changed in the conversation folder: orders-net.xlsx (3.0 MB). "
            "Attach one for the user with display_file."
        )
        assert "orders.xlsx (" not in result

    @pytest.mark.asyncio
    async def test_a_command_still_running_says_how_to_follow_it(self, sandbox: Any) -> None:
        sandbox.execute = AsyncMock(return_value={"status": "running", "id": "p1", "output": [], "truncated": True})

        result = await SandboxTools(_context()).run_command("sleep 999", wait=1000)

        assert sandbox.execute.await_args.kwargs["wait"] == 300
        assert result.startswith("Still running as process p1; check on it with get_process_status.")
        assert "The output was cut" in result

    @pytest.mark.asyncio
    async def test_a_displayed_file_is_kept_and_shown_on_the_answer(self, sandbox: Any, s3: Any) -> None:
        context = _context()

        result = await SandboxTools(context).display_file("chart.png")

        sandbox.view.assert_awaited_once_with(f"conversations/{THREAD}/chart.png")
        put = s3.put_object.call_args.kwargs
        assert put["Bucket"] == "agent-files"
        assert put["Key"].startswith("UniversalAgent/assistant/")
        assert put["Key"].endswith("/chart.png")
        assert put["Body"] == b"\x89PNG"
        shown = context.displayer.display_event.await_args.args[0]
        assert isinstance(shown, SandboxFileDisplayedEvent)
        assert (shown.filename, shown.content_type, shown.size, shown.key) == ("chart.png", "image/png", 4, put["Key"])
        assert result == (
            "Attached chart.png (4 bytes) to your answer; the user gets it with a download link, "
            "so do not attach it again."
        )

    @pytest.mark.asyncio
    async def test_a_user_without_a_chat_account_has_no_sandbox(self) -> None:
        tools = SandboxTools(_context())

        with (
            patch.object(sandbox_workspace.OpenWebuiAccountEntity, "openwebui_id_of", return_value=None),
            pytest.raises(OpenTerminalError, match="no code sandbox"),
        ):
            await tools.list_files()


class TestOffer:
    def test_every_sandbox_tool_needs_code_interpreter_switched_on(self) -> None:
        tool_set = ToolSet.of((SandboxTools,))

        assert {tool_set.options(name).chat_feature for name in tool_set.names()} == {ChatFeature.CODE_INTERPRETER}

    def test_the_universal_agent_offers_the_code_interpreter_toggle(self) -> None:
        assert ChatFeature.CODE_INTERPRETER in UniversalAgent.supported_features()


class TestUserFiles:
    @pytest.mark.asyncio
    async def test_the_listing_is_the_user_s_whole_file_space_without_dotfiles(self, sandbox: Any) -> None:
        sandbox.list_files = AsyncMock(
            return_value={
                "entries": [{"name": "conversations", "type": "directory"}, {"name": ".cache", "type": "directory"}]
            }
        )

        result = await UserFilesTools(_context()).list_my_files()

        sandbox.list_files.assert_awaited_once_with(".")
        assert "conversations" in result
        assert ".cache" not in result

    @pytest.mark.asyncio
    async def test_a_file_is_read_relative_to_the_top_not_the_conversation(self, sandbox: Any) -> None:
        sandbox.read_file = AsyncMock(return_value={"content": "25 days"})

        result = await UserFilesTools(_context()).read_my_file("reports/q1.pdf")

        sandbox.read_file.assert_awaited_once_with("reports/q1.pdf", None, None)
        assert "25 days" in result

    @pytest.mark.asyncio
    @pytest.mark.parametrize("path", ["/proc/1/environ", ".ssh/id_rsa", f"conversations/{THREAD}/.attached_files.json"])
    async def test_a_path_outside_the_user_s_files_is_refused(self, sandbox: Any, path: str) -> None:
        sandbox.read_file = AsyncMock()
        tools = UserFilesTools(_context())

        with pytest.raises(OpenTerminalError):
            await tools.read_my_file(path)
        sandbox.read_file.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_pages_of_a_pdf_are_read_through_the_platform_s_extraction(self, sandbox: Any) -> None:
        sandbox.view = AsyncMock(return_value=(b"%PDF", "application/pdf"))
        sandbox.read_file = AsyncMock()
        document = _extracted("one\n<!-- PageBreak -->\ntwo\n<!-- PageBreak -->\nthree", pages=3)

        with patch(
            f"{USER_FILE_PAGES}.DocumentExtractor.extract_from_bytes", AsyncMock(return_value=document)
        ) as extract:
            result = json.loads(
                await UserFilesTools(_context()).read_my_file("reports/q1.pdf", first_page=2, last_page=9)
            )

        extract.assert_awaited_once_with(b"%PDF", "q1.pdf", "application/pdf")
        sandbox.read_file.assert_not_awaited()
        assert result == {
            "path": "reports/q1.pdf",
            "number_of_pages": 3,
            "pages": [{"page": 2, "text": "two"}, {"page": 3, "text": "three"}],
        }

    @pytest.mark.asyncio
    async def test_a_document_without_page_marks_is_sent_back_to_reading_by_line(self, sandbox: Any) -> None:
        sandbox.view = AsyncMock(return_value=(b"PK", "application/vnd.openxmlformats-officedocument.wordprocessingml"))
        document = _extracted("all the text", pages=4)

        with patch(f"{USER_FILE_PAGES}.DocumentExtractor.extract_from_bytes", AsyncMock(return_value=document)):
            result = json.loads(await UserFilesTools(_context()).read_my_file("notes.docx", first_page=2))

        assert "read it by lines" in result["error"]

    def test_the_tools_need_my_files_switched_on(self) -> None:
        tool_set = ToolSet.of((UserFilesTools,))

        assert {tool_set.options(name).chat_feature for name in tool_set.names()} == {ChatFeature.USER_FILES}
        assert ChatFeature.USER_FILES in UniversalAgent.supported_features()
