import base64
from typing import Any

import pytest
from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError

from swiss_ai_hub.core.events.agent.control.start.rag_start_event import RAGStartEvent
from swiss_ai_hub.core.events.agent.control.start.start_event import StartEvent
from swiss_ai_hub.core.events.agent.user.inline_file import InlineFile
from swiss_ai_hub.core.events.agent.user.user_message_event import UserMessageEvent
from swiss_ai_hub.core.events.api_payload_context import ApiPayloadContext
from swiss_ai_hub.core.testing.auth_utils.test_identity import fake_user

UPLOADED_ID = "550e8400-e29b-41d4-a716-446655440000"
MESSAGES = [{"role": "user", "blocks": [{"block_type": "text", "text": "What does it say?"}]}]


class FakeS3:
    def __init__(self) -> None:
        self.objects: dict[tuple[str, str], tuple[bytes, str]] = {}

    def put_object(self, *, Bucket: str, Key: str, Body: bytes, ContentType: str) -> None:  # noqa: N803
        self.objects[(Bucket, Key)] = (Body, ContentType)


@pytest.fixture
def s3() -> FakeS3:
    return FakeS3()


@pytest.fixture
def context(s3: FakeS3) -> ApiPayloadContext:
    return ApiPayloadContext(user=fake_user(), locale="fr", agent_class="Rag", agent_id="a1", s3_client=s3)


def inline(filename: str, content: bytes, file_type: str = "text/plain") -> dict[str, Any]:
    return {"filename": filename, "file_type": file_type, "content": base64.b64encode(content).decode()}


async def user_message(payload: dict[str, Any], context: ApiPayloadContext) -> UserMessageEvent:
    return await StartEvent.from_api_payload(
        payload,
        event_name="UserMessageEvent",
        event_parents=UserMessageEvent.parent_event_names_from_class(),
        context=context,
    )


class TestApiInputModel:
    def test_leaves_out_what_the_server_fills_in(self):
        fields = set(UserMessageEvent.api_input_model().model_fields)
        assert not fields & {"event_id", "created_at", "user", "locale", "display_name", "display_description"}
        assert "messages" in fields

    def test_files_accept_references_and_inline_files(self):
        schema = UserMessageEvent.api_input_model().model_json_schema()
        items = schema["properties"]["files"]["anyOf"][0]["items"]["anyOf"]
        assert {"$ref": "#/$defs/UserUploadedFile"} in items
        assert {"$ref": "#/$defs/InlineFile"} in items
        assert schema["$defs"]["InlineFile"]["properties"]["content"]["contentEncoding"] == "base64"

    def test_the_agent_facing_event_keeps_references_only(self):
        files_schema = UserMessageEvent.model_json_schema()["properties"]["files"]
        assert "InlineFile" not in str(files_schema)


@pytest.mark.asyncio
class TestFromApiPayload:
    async def test_stores_inline_files_and_keeps_the_callers_order(self, context: ApiPayloadContext, s3: FakeS3):
        uploaded = {"filename": "old.pdf", "file_type": "application/pdf", "file_id": UPLOADED_ID}
        payload = {"messages": MESSAGES, "files": [inline("a.txt", b"first"), uploaded, inline("b.md", b"second")]}

        event = await user_message(payload, context)

        assert [file.filename for file in event.files] == ["a.txt", "old.pdf", "b.md"]
        assert event.files[1].file_id == UPLOADED_ID
        stored = {key: body for (_, key), (body, _) in s3.objects.items()}
        assert stored == {
            f"Rag/a1/{event.files[0].file_id}/a.txt": b"first",
            f"Rag/a1/{event.files[2].file_id}/b.md": b"second",
        }
        assert "Zmlyc3Q" not in event.model_dump_json()

    async def test_fills_in_the_caller_and_locale(self, context: ApiPayloadContext):
        event = await user_message({"messages": MESSAGES, "user": {"id": "spoofed"}, "locale": "de"}, context)
        assert event.user.id == context.user.id
        assert event.locale == "fr"

    async def test_one_bad_file_stores_nothing(self, context: ApiPayloadContext, s3: FakeS3):
        payload = {"messages": MESSAGES, "files": [inline("a.txt", b"fine"), inline("b.zip", b"PK", "application/zip")]}

        with pytest.raises(HTTPException) as rejected:
            await user_message(payload, context)

        assert rejected.value.status_code == 415
        assert "b.zip" in rejected.value.detail
        assert s3.objects == {}

    async def test_an_agent_only_subclass_uses_its_parents_conversion(self, context: ApiPayloadContext, s3: FakeS3):
        payload = {"messages": MESSAGES, "files": [inline("a.txt", b"hi")], "ticket": "T-1"}

        event = await StartEvent.from_api_payload(
            payload,
            event_name="TicketMessageEvent",
            event_parents=["TicketMessageEvent", *UserMessageEvent.parent_event_names_from_class()],
            context=context,
        )

        assert isinstance(event, UserMessageEvent)
        assert event.files[0].filename == "a.txt"
        assert event.model_extra["ticket"] == "T-1"
        assert len(s3.objects) == 1

    async def test_rag_start_event_converts_its_files_too(self, context: ApiPayloadContext, s3: FakeS3):
        event = await StartEvent.from_api_payload(
            {"messages": MESSAGES, "selected_namespaces": [], "files": [inline("a.txt", b"hi")]},
            event_name="RAGStartEvent",
            event_parents=RAGStartEvent.parent_event_names_from_class(),
            context=context,
        )
        assert event.files[0].filename == "a.txt"
        assert len(s3.objects) == 1

    async def test_an_invalid_payload_is_a_validation_error(self, context: ApiPayloadContext):
        with pytest.raises(RequestValidationError):
            await user_message({"messages": "not a list"}, context)


@pytest.mark.asyncio
class TestStoreAll:
    async def test_rejects_invalid_base64(self, context: ApiPayloadContext):
        with pytest.raises(HTTPException) as rejected:
            await InlineFile.store_all(
                [InlineFile(filename="a.txt", file_type="text/plain", content="not base64!")], context
            )
        assert rejected.value.status_code == 422

    async def test_rejects_a_file_over_the_limit(self, context: ApiPayloadContext, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("AGENT_INLINE_FILE_MAX_FILE_BYTES", "4")
        with pytest.raises(HTTPException) as rejected:
            await InlineFile.store_all([InlineFile(**inline("a.txt", b"12345"))], context)
        assert rejected.value.status_code == 413

    async def test_rejects_too_many_files(self, context: ApiPayloadContext, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("AGENT_INLINE_FILE_MAX_FILES_PER_REQUEST", "1")
        files = [InlineFile(**inline("a.txt", b"a")), InlineFile(**inline("b.txt", b"b"))]
        with pytest.raises(HTTPException) as rejected:
            await InlineFile.store_all(files, context)
        assert rejected.value.status_code == 413

    async def test_points_images_to_image_url(self, context: ApiPayloadContext):
        with pytest.raises(HTTPException) as rejected:
            await InlineFile.store_all([InlineFile(**inline("a.png", b"\x89PNG", "image/png"))], context)
        assert rejected.value.status_code == 415
        assert "image_url" in rejected.value.detail
