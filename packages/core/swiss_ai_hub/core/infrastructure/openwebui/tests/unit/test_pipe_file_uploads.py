"""How the OpenWebUI pipe hands a turn's files to the agent's bucket: one validate call for the uploads it knows, and
one more only after uploading what the bucket lacked, so the API places the turn's files together, once. A temporary
chat's text items are remembered in Open WebUI's Redis, so they are uploaded once too."""

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
OPEN_WEBUI_MODULES += ["open_webui.models.users", "open_webui.utils", "open_webui.utils.chat_id"]
OPEN_WEBUI_MODULES += ["open_webui.models.notes", "open_webui.models.access_grants", "open_webui.models.folders"]
OPEN_WEBUI_MODULES += ["open_webui.utils.misc", "open_webui.utils.access_control", "open_webui.utils.access_control.folders"]

AGENT_CLASS, AGENT_ID = "RAGAgent", "hr"
THREAD = "65f1c0ffee00000000000001"
USER = "user-1"
SEVEN_DAYS = 604800


def _is_saved_chat_id(chat_id: str | None) -> bool:
    """Open WebUI 0.11.3's own rule, since a stubbed one would call every chat saved."""
    return bool(chat_id) and not chat_id.startswith(("temporary:", "local:", "channel:"))


@pytest.fixture
def pipe(monkeypatch: pytest.MonkeyPatch) -> Any:
    for name in OPEN_WEBUI_MODULES:
        monkeypatch.setitem(sys.modules, name, MagicMock())
    sys.modules["open_webui.utils.chat_id"].is_saved_chat_id = _is_saved_chat_id
    spec = importlib.util.spec_from_file_location("aihub_pipeline", TEMPLATE_PIPE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _Response:
    def __init__(self, body: dict[str, Any]) -> None:
        self._body = body

    def json(self) -> dict[str, Any]:
        return self._body

    def raise_for_status(self) -> None:
        return None


class _AgentFilesApi:
    """The agent file endpoints and the bucket behind them, recording every validate call and upload."""

    def __init__(self, error: type[Exception], stored: set[str] | None = None) -> None:
        self.stored = set(stored or ())
        self.validations: list[dict[str, Any]] = []
        self.uploads: list[bytes] = []
        self.failing_validations = 0
        self.malformed_validations = 0
        self._error = error

    def client(self, **_: Any) -> "_AgentFilesApi":
        return self

    async def __aenter__(self) -> "_AgentFilesApi":
        return self

    async def __aexit__(self, *_: Any) -> None:
        return None

    async def post(self, url: str, headers: dict[str, str], json: dict[str, Any]) -> _Response:
        if url.endswith("/validate"):
            self.validations.append(json)
            if self.failing_validations:
                self.failing_validations -= 1
                raise self._error("the API is unavailable")
            if self.malformed_validations:
                self.malformed_validations -= 1
                return _Response({"detail": "a proxy's error page"})
            return _Response(
                {"missing": [file["file_id"] for file in json["files"] if file["file_id"] not in self.stored]}
            )
        file_id = f"00000000-0000-4000-a000-{len(self.uploads) + 1:012d}"
        return _Response({"file_id": file_id, "upload_url": f"http://s3/{file_id}"})

    async def put(self, url: str, content: bytes, headers: dict[str, str]) -> _Response:
        self.uploads.append(content)
        self.stored.add(url.rsplit("/", 1)[1])
        return _Response({})


class _Redis:
    def __init__(self, failing_reads: bool = False) -> None:
        self.values: dict[str, str] = {}
        self.expiries: dict[str, int | None] = {}
        self.failing_reads = failing_reads

    async def get(self, key: str) -> str | None:
        if self.failing_reads:
            raise ConnectionError("Redis is unavailable")
        return self.values.get(key)

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        self.values[key] = value
        self.expiries[key] = ex


def _known_id(number: int) -> str:
    return f"aaaaaaaa-0000-4000-a000-{number:012d}"


def _owui_file(owui_id: str, name: str, known_file_id: str | None = None) -> MagicMock:
    uploads = {f"{AGENT_CLASS}/{AGENT_ID}": known_file_id} if known_file_id else {}
    meta = {"name": name, "content_type": "application/pdf", "aihub_agent_uploads": uploads}
    return MagicMock(id=owui_id, path=f"s3://openwebui/{owui_id}_{name}", meta=meta)


def _service(pipe: Any, monkeypatch: pytest.MonkeyPatch, api: _AgentFilesApi, *owui_files: MagicMock) -> Any:
    by_id = {file.id: file for file in owui_files}
    pipe.Files.get_file_by_id = AsyncMock(side_effect=by_id.get)
    pipe.Files.update_file_metadata_by_id = AsyncMock()
    monkeypatch.setattr(pipe.httpx, "AsyncClient", api.client)
    service = pipe.FileProcessingService.__new__(pipe.FileProcessingService)
    service._base_url = "http://api"
    service._owui_s3_client = MagicMock()
    service._owui_s3_client.get_object.side_effect = lambda Bucket, Key: {"Body": io.BytesIO(Key.encode())}
    return service


async def _turn(
    service: Any, files: list[dict[str, Any]], redis: Any = None, user: str = USER
) -> tuple[list[dict[str, str]], dict]:
    return await service.prepare_files_for_event(files, AGENT_CLASS, AGENT_ID, {}, THREAD, user, redis)


def _checked(validation: dict[str, Any]) -> list[str]:
    return [file["file_id"] for file in validation["files"]]


@pytest.mark.asyncio
async def test_known_files_cost_one_validate_call(pipe: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    owui_files = [_owui_file(f"owui-{number}", f"doc{number}.pdf", _known_id(number)) for number in range(3)]
    api = _AgentFilesApi(pipe.httpx.HTTPError, stored={_known_id(number) for number in range(3)})
    service = _service(pipe, monkeypatch, api, *owui_files)

    files, owui_file_ids = await _turn(service, [{"type": "file", "id": file.id} for file in owui_files])

    assert len(api.validations) == 1
    assert api.validations[0]["thread_id"] == THREAD
    assert _checked(api.validations[0]) == [_known_id(0), _known_id(1), _known_id(2)]
    assert api.uploads == []
    assert [file["file_id"] for file in files] == [_known_id(0), _known_id(1), _known_id(2)]
    assert owui_file_ids == {_known_id(number): f"owui-{number}" for number in range(3)}


@pytest.mark.asyncio
async def test_a_missing_file_is_uploaded_again_and_all_the_turn_s_files_checked_once_more(
    pipe: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    kept, expired = _owui_file("owui-0", "kept.pdf", _known_id(0)), _owui_file("owui-1", "gone.pdf", _known_id(1))
    api = _AgentFilesApi(pipe.httpx.HTTPError, stored={_known_id(0)})
    service = _service(pipe, monkeypatch, api, kept, expired)

    files, owui_file_ids = await _turn(service, [{"type": "file", "id": "owui-0"}, {"type": "file", "id": "owui-1"}])

    reuploaded = files[1]["file_id"]
    assert api.uploads == [b"owui-1_gone.pdf"]
    assert len(api.validations) == 2
    assert _checked(api.validations[0]) == [_known_id(0), _known_id(1)]
    assert _checked(api.validations[1]) == [_known_id(0), reuploaded]
    assert api.validations[1]["thread_id"] == THREAD
    assert owui_file_ids == {_known_id(0): "owui-0", reuploaded: "owui-1"}
    pipe.Files.update_file_metadata_by_id.assert_awaited_once_with(
        "owui-1", {"aihub_agent_uploads": {f"{AGENT_CLASS}/{AGENT_ID}": reuploaded}}
    )


@pytest.mark.asyncio
async def test_a_turn_with_a_new_file_is_placed_only_on_the_check_after_its_upload(
    pipe: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    api = _AgentFilesApi(pipe.httpx.HTTPError, stored={_known_id(0)})
    service = _service(
        pipe, monkeypatch, api, _owui_file("owui-0", "kept.pdf", _known_id(0)), _owui_file("owui-1", "new.pdf")
    )

    files, _ = await _turn(service, [{"type": "file", "id": "owui-0"}, {"type": "file", "id": "owui-1"}])

    assert [validation["thread_id"] for validation in api.validations] == [None, THREAD]
    assert _checked(api.validations[0]) == [_known_id(0)]
    assert _checked(api.validations[1]) == [file["file_id"] for file in files]
    assert len(files) == 2


@pytest.mark.asyncio
async def test_a_temporary_chat_s_text_is_uploaded_once_and_reused_on_the_next_turn(
    pipe: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    api = _AgentFilesApi(pipe.httpx.HTTPError)
    service = _service(pipe, monkeypatch, api)
    redis = _Redis()
    item = {"type": "text", "id": "item-1", "name": "notes", "content": "hello"}

    first, first_owui_ids = await _turn(service, [item], redis)
    second, _ = await _turn(service, [item], redis)

    assert api.uploads == [b"hello"]
    assert first == second == [{"filename": "notes.txt", "file_type": "text/plain", "file_id": first[0]["file_id"]}]
    assert first_owui_ids == {}
    key = f"aihub:temp-upload:{USER}:{THREAD}:item-1"
    assert (redis.values[key], redis.expiries[key]) == (first[0]["file_id"], SEVEN_DAYS)
    assert len(api.validations) == 2
    assert all(validation["thread_id"] == THREAD for validation in api.validations)


@pytest.mark.asyncio
async def test_without_redis_a_temporary_chat_s_text_is_uploaded_every_turn(
    pipe: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    api = _AgentFilesApi(pipe.httpx.HTTPError)
    service = _service(pipe, monkeypatch, api)
    item = {"type": "text", "id": "item-1", "name": "notes.txt", "content": "hello"}

    first, _ = await _turn(service, [item])
    second, _ = await _turn(service, [item])

    assert api.uploads == [b"hello", b"hello"]
    assert first[0]["file_id"] != second[0]["file_id"]
    assert len(api.validations) == 2


@pytest.mark.asyncio
async def test_a_failed_check_uploads_the_files_again_instead_of_failing_the_turn(
    pipe: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    api = _AgentFilesApi(pipe.httpx.HTTPError, stored={_known_id(0)})
    api.failing_validations = 1
    service = _service(pipe, monkeypatch, api, _owui_file("owui-0", "kept.pdf", _known_id(0)))

    files, _ = await _turn(service, [{"type": "file", "id": "owui-0"}])

    assert api.uploads == [b"owui-0_kept.pdf"]
    assert len(api.validations) == 2
    assert _checked(api.validations[1]) == [files[0]["file_id"]]


@pytest.mark.asyncio
async def test_a_file_that_fails_to_upload_leaves_the_others_in_the_turn(
    pipe: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    api = _AgentFilesApi(pipe.httpx.HTTPError, stored={_known_id(0)})
    broken = _owui_file("owui-1", "broken.pdf")
    broken.path = "file:///nowhere/broken.pdf"
    service = _service(pipe, monkeypatch, api, _owui_file("owui-0", "kept.pdf", _known_id(0)), broken)

    files, _ = await _turn(service, [{"type": "file", "id": "owui-0"}, {"type": "file", "id": "owui-1"}])

    assert [file["file_id"] for file in files] == [_known_id(0)]
    assert [validation["thread_id"] for validation in api.validations] == [None, THREAD]
    assert _checked(api.validations[1]) == [_known_id(0)]


@pytest.mark.asyncio
@pytest.mark.parametrize(("chat_id", "saved"), [("chat-1", True), ("temporary:abc", False), ("channel:c1", False)])
async def test_only_a_saved_chat_gets_the_agent_s_title(pipe: Any, chat_id: str, saved: bool) -> None:
    pipe.Chats.update_chat_title_by_id = AsyncMock()
    emitter = AsyncMock()
    context = pipe.EventContext(
        state_manager=pipe.StreamingStateManager(),
        emitter=emitter,
        caller=MagicMock(),
        headers={},
        agent_class=AGENT_CLASS,
        agent_id=AGENT_ID,
        thread_id=THREAD,
        stream_service=MagicMock(),
        chat_id=chat_id,
    )

    await pipe.ConversationTitleEventHandler().handle({"title": "Leave policy"}, context)

    assert pipe.Chats.update_chat_title_by_id.await_count == int(saved)
    emitter.assert_awaited_once_with({"type": "chat:title", "data": "Leave policy"})


@pytest.mark.asyncio
async def test_a_redis_read_error_uploads_the_temporary_text_instead_of_dropping_it(
    pipe: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    api = _AgentFilesApi(pipe.httpx.HTTPError)
    service = _service(pipe, monkeypatch, api)
    item = {"type": "text", "id": "item-1", "name": "notes", "content": "hello"}

    files, _ = await _turn(service, [item], _Redis(failing_reads=True))

    assert api.uploads == [b"hello"]
    assert [file["filename"] for file in files] == ["notes.txt"]


@pytest.mark.asyncio
async def test_another_user_never_reuses_a_temporary_chat_s_upload(pipe: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    """A temporary chat's id comes from the browser, so it alone must not lead to someone else's upload."""
    api = _AgentFilesApi(pipe.httpx.HTTPError)
    service = _service(pipe, monkeypatch, api)
    redis = _Redis()
    item = {"type": "text", "id": "item-1", "name": "notes", "content": "hello"}

    mine, _ = await _turn(service, [item], redis, user="user-1")
    theirs, _ = await _turn(service, [item], redis, user="user-2")

    assert mine[0]["file_id"] != theirs[0]["file_id"]
    assert api.uploads == [b"hello", b"hello"]


def _notes(*notes: MagicMock, shared_with: str | None = None) -> None:
    """Open WebUI's notes and the read grants on them, which the pipe imports only once a note is attached."""
    by_id = {note.id: note for note in notes}
    sys.modules["open_webui.models.notes"].Notes.get_note_by_id = AsyncMock(side_effect=by_id.get)
    sys.modules["open_webui.models.access_grants"].AccessGrants.has_access = AsyncMock(
        side_effect=lambda user_id, **_: user_id == shared_with
    )


def _note(markdown: str, updated_at: int = 1, owner: str = USER) -> MagicMock:
    note = MagicMock(id="note-1", user_id=owner, updated_at=updated_at, data={"content": {"md": markdown}})
    note.title = "Vocabulary"
    return note


@pytest.mark.asyncio
async def test_an_attached_note_reaches_the_agent_as_markdown_once_per_version(
    pipe: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    api = _AgentFilesApi(pipe.httpx.HTTPError)
    service = _service(pipe, monkeypatch, api)
    redis = _Redis()
    item = {"type": "note", "id": "note-1", "name": "Vocabulary"}

    _notes(_note("# Words"))
    first, owui_file_ids = await _turn(service, [item], redis)
    second, _ = await _turn(service, [item], redis)
    _notes(_note("# Words\n- abate", updated_at=2))
    edited, _ = await _turn(service, [item], redis)

    assert api.uploads == [b"# Words", b"# Words\n- abate"]
    assert (
        first == second == [{"filename": "Vocabulary.md", "file_type": "text/markdown", "file_id": first[0]["file_id"]}]
    )
    assert edited[0]["file_id"] != first[0]["file_id"]
    assert owui_file_ids == {}
    assert redis.values[f"aihub:temp-upload:{USER}:{THREAD}:note:note-1:1"] == first[0]["file_id"]


@pytest.mark.asyncio
@pytest.mark.parametrize(("owner", "shared_with", "read"), [("user-2", USER, True), ("user-2", None, False)])
async def test_another_user_s_note_reaches_the_agent_only_when_shared_with_the_user(
    pipe: Any, monkeypatch: pytest.MonkeyPatch, owner: str, shared_with: str | None, read: bool
) -> None:
    """The pipe reads Open WebUI's database with its own rights, so a note id alone must not reveal the note."""
    api = _AgentFilesApi(pipe.httpx.HTTPError)
    service = _service(pipe, monkeypatch, api)
    _notes(_note("secret", owner=owner), shared_with=shared_with)

    files, _ = await _turn(service, [{"type": "note", "id": "note-1"}])

    assert api.uploads == ([b"secret"] if read else [])
    assert len(files) == int(read)


@pytest.mark.asyncio
async def test_a_deleted_note_is_left_out_of_the_turn(pipe: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    api = _AgentFilesApi(pipe.httpx.HTTPError)
    service = _service(pipe, monkeypatch, api)
    _notes()

    files, _ = await _turn(service, [{"type": "note", "id": "note-1"}])

    assert files == []
    assert api.uploads == []


def _message_list(messages_map: dict[str, dict[str, Any]], message_id: str) -> list[dict[str, Any]]:
    """Open WebUI 0.11.3's walk from the current message up to the first, since the transcript follows that branch."""
    branch = []
    while message_id:
        branch.append(messages_map[message_id])
        message_id = messages_map[message_id].get("parentId")
    return branch[::-1]


def _chats(
    *chats: MagicMock, pipe: Any, shared_with: str | None = None, folder_readers: tuple[str, ...] = ()
) -> None:
    """Open WebUI's chats, the read grants on them and their folders' readers, as the pipe sees them."""
    by_id = {chat.id: chat for chat in chats}
    pipe.Chats.get_chat_by_id = AsyncMock(side_effect=by_id.get)
    sys.modules["open_webui.models.access_grants"].AccessGrants.has_access = AsyncMock(
        side_effect=lambda user_id, **_: user_id == shared_with
    )
    sys.modules["open_webui.models.folders"].Folders.get_folder_by_id = AsyncMock(
        side_effect=lambda folder_id: MagicMock(id=folder_id)
    )
    sys.modules["open_webui.utils.access_control.folders"].has_folder_access = AsyncMock(
        side_effect=lambda user_id, *_, **__: user_id in folder_readers
    )
    misc = sys.modules["open_webui.utils.misc"]
    misc.get_message_list = _message_list
    misc.get_content_from_message = lambda message: message.get("content")


def _chat(*turns: tuple[str, str], updated_at: int = 1, owner: str = USER, folder_id: str | None = None) -> MagicMock:
    messages = {
        f"m{index}": {"id": f"m{index}", "parentId": f"m{index - 1}" if index else None, "role": role, "content": text}
        for index, (role, text) in enumerate(turns)
    }
    history = {"messages": messages, "currentId": f"m{len(turns) - 1}"}
    chat = MagicMock(id="chat-1", user_id=owner, updated_at=updated_at, folder_id=folder_id, chat={"history": history})
    chat.title = "Inquiry About Tuan"
    return chat


@pytest.mark.asyncio
async def test_an_attached_chat_reaches_the_agent_as_its_transcript_once_per_version(
    pipe: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    api = _AgentFilesApi(pipe.httpx.HTTPError)
    service = _service(pipe, monkeypatch, api)
    redis = _Redis()
    item = {"type": "chat", "id": "chat-1", "name": "Inquiry About Tuan"}
    asked = (("user", "Who is Tuan?"), ("assistant", "Tuan leads the QC team."))

    _chats(_chat(*asked), pipe=pipe)
    first, owui_file_ids = await _turn(service, [item], redis)
    second, _ = await _turn(service, [item], redis)
    _chats(_chat(*asked, ("user", "And his email?"), updated_at=2), pipe=pipe)
    grown, _ = await _turn(service, [item], redis)

    transcript = "#### User\nWho is Tuan?\n\n#### Assistant\nTuan leads the QC team.\n"
    assert api.uploads == [transcript.encode(), f"{transcript}\n#### User\nAnd his email?\n".encode()]
    assert first == second
    assert first == [
        {"filename": "Inquiry About Tuan.md", "file_type": "text/markdown", "file_id": first[0]["file_id"]}
    ]
    assert grown[0]["file_id"] != first[0]["file_id"]
    assert owui_file_ids == {}
    assert redis.values[f"aihub:temp-upload:{USER}:{THREAD}:chat:chat-1:1"] == first[0]["file_id"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("shared_with", "folder_readers", "read"),
    [(USER, (), True), (None, (USER,), True), (None, (), False)],
    ids=["shared", "in-a-readable-folder", "neither"],
)
async def test_another_user_s_chat_reaches_the_agent_only_when_the_user_may_read_it(
    pipe: Any,
    monkeypatch: pytest.MonkeyPatch,
    shared_with: str | None,
    folder_readers: tuple[str, ...],
    read: bool,
) -> None:
    """The pipe reads Open WebUI's database with its own rights, so a chat id alone must not reveal the chat."""
    api = _AgentFilesApi(pipe.httpx.HTTPError)
    service = _service(pipe, monkeypatch, api)
    secret = _chat(("user", "secret"), owner="user-2", folder_id="folder-1")
    _chats(secret, pipe=pipe, shared_with=shared_with, folder_readers=folder_readers)

    files, _ = await _turn(service, [{"type": "chat", "id": "chat-1"}])

    assert api.uploads == ([b"#### User\nsecret\n"] if read else [])
    assert len(files) == int(read)


@pytest.mark.asyncio
async def test_a_chat_titled_with_a_path_separator_still_reaches_the_agent(
    pipe: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The agent upload API refuses a filename with a path separator, which a chat's title may hold."""
    api = _AgentFilesApi(pipe.httpx.HTTPError)
    service = _service(pipe, monkeypatch, api)
    chat = _chat(("user", "Plan?"))
    chat.title = "Q1/Q2 plan\\" + "x" * 300
    _chats(chat, pipe=pipe)

    files, _ = await _turn(service, [{"type": "chat", "id": "chat-1"}])

    assert files[0]["filename"].startswith("Q1-Q2 plan-x")
    assert files[0]["filename"].endswith(".md")
    assert len(files[0]["filename"]) == 255


@pytest.mark.asyncio
async def test_a_chat_without_messages_is_left_out_of_the_turn(pipe: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    api = _AgentFilesApi(pipe.httpx.HTTPError)
    service = _service(pipe, monkeypatch, api)
    empty = _chat(("user", "x"))
    empty.chat = {"history": {"messages": {}, "currentId": None}}
    _chats(empty, pipe=pipe)

    files, _ = await _turn(service, [{"type": "chat", "id": "chat-1"}])

    assert files == []
    assert api.uploads == []


@pytest.mark.asyncio
async def test_a_deleted_chat_is_left_out_of_the_turn(pipe: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    api = _AgentFilesApi(pipe.httpx.HTTPError)
    service = _service(pipe, monkeypatch, api)
    _chats(pipe=pipe)

    files, _ = await _turn(service, [{"type": "chat", "id": "chat-1"}])

    assert files == []
    assert api.uploads == []


@pytest.mark.asyncio
async def test_a_malformed_validate_answer_counts_as_a_failed_check(pipe: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    api = _AgentFilesApi(pipe.httpx.HTTPError, stored={_known_id(0)})
    api.malformed_validations = 1
    service = _service(pipe, monkeypatch, api, _owui_file("owui-0", "kept.pdf", _known_id(0)))

    files, _ = await _turn(service, [{"type": "file", "id": "owui-0"}])

    assert api.uploads == [b"owui-0_kept.pdf"]
    assert [file["file_id"] for file in files] == [_checked(api.validations[1])[0]]
