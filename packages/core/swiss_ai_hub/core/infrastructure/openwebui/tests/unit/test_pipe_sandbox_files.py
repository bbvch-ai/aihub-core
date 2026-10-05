"""How the OpenWebUI pipe attaches a file the agent showed from the user's code sandbox: read from our storage,
registered as an Open WebUI file, linked to the chat message and added to the answer's files."""

import importlib.util
import io
import sys
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

pytestmark = pytest.mark.unit

REPO_ROOT = Path(__file__).resolve().parents[8]
TEMPLATE_PIPE = REPO_ROOT / "infra/deployment/templates/openwebui_functions/aihub_pipeline.py"
OPEN_WEBUI_MODULES = ["open_webui", "open_webui.models", "open_webui.models.chats", "open_webui.models.files"]
OPEN_WEBUI_MODULES += ["open_webui.models.users", "open_webui.routers", "open_webui.routers.files"]

DISPLAYED = {
    "_event_name": "SandboxFileDisplayedEvent",
    "path": "/home/u/conversations/t1/chart.png",
    "filename": "chart.png",
    "content_type": "image/png",
    "size": 4,
    "bucket": "agent-files",
    "key": "UniversalAgent/assistant/abc/chart.png",
}


@pytest.fixture
def pipe(monkeypatch: pytest.MonkeyPatch) -> Any:
    for name in OPEN_WEBUI_MODULES:
        monkeypatch.setitem(sys.modules, name, MagicMock())
    spec = importlib.util.spec_from_file_location("aihub_pipeline", TEMPLATE_PIPE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _Recorder:
    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    async def __call__(self, event: dict[str, Any]) -> None:
        self.events.append(event)


def _service(pipe: Any) -> tuple[Any, MagicMock, MagicMock]:
    s3 = MagicMock()
    s3.get_object.return_value = {"Body": io.BytesIO(b"\x89PNG")}
    request = MagicMock()
    request.app.url_path_for.return_value = "/api/v1/files/f1/content"
    return pipe.AgentFileAttachmentService(s3, request, "owui-user"), s3, request


def _uploaded(pipe: Any) -> AsyncMock:
    upload = sys.modules["open_webui.routers.files"].upload_file_handler = AsyncMock(return_value=MagicMock(id="f1"))
    pipe.Users.get_user_by_id = AsyncMock(return_value=MagicMock(id="owui-user"))
    pipe.Chats.insert_chat_files = AsyncMock()
    return upload


@pytest.mark.asyncio
async def test_a_displayed_file_joins_the_answer_s_files(pipe: Any) -> None:
    """The server keeps the new file next to the earlier ones; the browser is given all of them, since it replaces."""
    attachments = MagicMock()
    attachments.attach = AsyncMock(return_value={"type": "file", "id": "f2", "name": "chart.png"})
    attachments.attached = [
        {"type": "file", "id": "f1", "name": "totals.xlsx"},
        {"type": "file", "id": "f2", "name": "chart.png"},
    ]
    emitter = _Recorder()
    context = pipe.EventContext(
        state_manager=pipe.StreamingStateManager(),
        emitter=emitter,
        caller=MagicMock(),
        headers={},
        agent_class="UniversalAgent",
        agent_id="assistant",
        thread_id="t1",
        stream_service=MagicMock(),
        chat_id="chat-1",
        message_id="msg-1",
        attachments=attachments,
    )

    await pipe.SandboxFileDisplayedEventHandler().handle(DISPLAYED, context)

    attachments.attach.assert_awaited_once_with(DISPLAYED, "chat-1", "msg-1")
    assert emitter.events == [
        {"type": "files", "data": {"files": [{"type": "file", "id": "f2", "name": "chart.png"}]}},
        {"type": "chat:message:files", "data": {"files": attachments.attached}},
    ]


@pytest.mark.asyncio
async def test_the_copy_is_registered_unprocessed_and_linked_to_the_message(pipe: Any) -> None:
    upload = _uploaded(pipe)
    service, s3, _ = _service(pipe)

    attached = await service.attach(DISPLAYED, "chat-1", "msg-1")

    s3.get_object.assert_called_once_with(Bucket="agent-files", Key="UniversalAgent/assistant/abc/chart.png")
    kwargs = upload.await_args.kwargs
    assert kwargs["process"] is False
    assert kwargs["file"].filename == "chart.png"
    assert kwargs["metadata"] == {"chat_id": "chat-1", "message_id": "msg-1"}
    pipe.Chats.insert_chat_files.assert_awaited_once_with(
        chat_id="chat-1", message_id="msg-1", file_ids=["f1"], user_id="owui-user"
    )
    assert service.attached == [attached]
    assert attached == {
        "type": "file",
        "id": "f1",
        "url": "/api/v1/files/f1/content",
        "name": "chart.png",
        "content_type": "image/png",
        "size": 4,
    }


@pytest.mark.asyncio
async def test_a_temporary_chat_gets_the_file_without_a_message_link(pipe: Any) -> None:
    _uploaded(pipe)
    service, _, _ = _service(pipe)

    attached = await service.attach(DISPLAYED, "local:abc", "msg-1")

    pipe.Chats.insert_chat_files.assert_not_awaited()
    assert attached["id"] == "f1"


@pytest.mark.asyncio
async def test_the_answer_links_each_attached_file_once(pipe: Any) -> None:
    """Open WebUI offers an attachment's download only behind its name in the preview, so the answer links it."""
    _uploaded(pipe)
    service, _, _ = _service(pipe)
    await service.attach(DISPLAYED, "chat-1", "msg-1")

    assert service.download_links() == "\n\nDownload: [chart.png](/api/v1/files/f1/content)"
    assert service.download_links() == ""


@pytest.mark.asyncio
async def test_an_earlier_answer_reaches_the_agent_without_its_download_links(pipe: Any) -> None:
    """A model handed the earlier link reuses its url for the file it makes next, which then downloads the old one."""
    _uploaded(pipe)
    service, _, _ = _service(pipe)
    await service.attach(DISPLAYED, "chat-1", "msg-1")
    answer = "The chart is attached." + service.download_links()

    converted = pipe.MessageConverter.convert_to_event_format(
        [{"role": "assistant", "content": answer}, {"role": "user", "content": "Now make a spreadsheet."}]
    )

    assert converted[0]["blocks"][0]["text"] == "The chart is attached."


def test_a_download_line_a_model_copied_leaves_the_history_too(pipe: Any) -> None:
    """The copy carries the new file's name over the earlier file's url, as in the answer the issue shows."""
    answer = (
        "4. Monthly Revenue Chart\nI have generated a chart.\n\n"
        "Download: [monthly_revenue_chart.png](/api/v1/files/xlsx-id/content)\n\n"
        "Download: [monthly_revenue_chart.png](/api/v1/files/png-id/content) · [totals.xlsx](/api/v1/files/t/content)"
    )

    converted = pipe.MessageConverter.convert_to_event_format([{"role": "assistant", "content": answer}])

    assert converted[0]["blocks"][0]["text"] == "4. Monthly Revenue Chart\nI have generated a chart."


def test_a_file_linked_in_the_prose_keeps_its_name_without_its_url(pipe: Any) -> None:
    answer = "Open [the chart](/api/v1/files/f1/content) or see ![preview](/api/v1/files/f1/content) below."
    question = "Is [this](/api/v1/files/f9/content) the right file?"

    converted = pipe.MessageConverter.convert_to_event_format(
        [{"role": "assistant", "content": answer}, {"role": "user", "content": question}]
    )

    assert converted[0]["blocks"][0]["text"] == "Open the chart or see preview below."
    assert converted[1]["blocks"][0]["text"] == question
