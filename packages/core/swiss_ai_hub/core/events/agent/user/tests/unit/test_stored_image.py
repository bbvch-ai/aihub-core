import base64
from typing import Any

import pytest
from botocore.exceptions import ClientError
from fastapi import HTTPException

from swiss_ai_hub.core.events.agent.control.start.start_event import StartEvent
from swiss_ai_hub.core.events.agent.user.user_message_event import UserMessageEvent
from swiss_ai_hub.core.events.api_payload_context import ApiPayloadContext
from swiss_ai_hub.core.testing.auth_utils.test_identity import fake_user

PNG = base64.b64encode(b"\x89PNG not really").decode()
FOLDER = "s3://agent-files/Universal/a1/images/"


class FakeS3:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}
        self.puts = 0

    def put_object(self, *, Bucket: str, Key: str, Body: bytes, ContentType: str) -> None:  # noqa: N803
        self.objects[Key] = Body
        self.puts += 1

    def head_object(self, *, Bucket: str, Key: str) -> None:  # noqa: N803
        if Key not in self.objects:
            raise ClientError({"Error": {"Code": "404"}}, "HeadObject")


@pytest.fixture
def s3() -> FakeS3:
    return FakeS3()


@pytest.fixture
def context(s3: FakeS3) -> ApiPayloadContext:
    return ApiPayloadContext(user=fake_user(), locale="en", agent_class="Universal", agent_id="a1", s3_client=s3)


def image_message(*blocks: dict[str, Any]) -> dict[str, Any]:
    return {"role": "user", "blocks": [{"block_type": "text", "text": "What is this?"}, *blocks]}


def data_url(content: str = PNG, media_type: str = "image/png") -> dict[str, Any]:
    return {"block_type": "image", "url": f"data:{media_type};base64,{content}"}


async def send(payload: dict[str, Any], context: ApiPayloadContext) -> UserMessageEvent:
    return await StartEvent.from_api_payload(
        payload,
        event_name="UserMessageEvent",
        event_parents=UserMessageEvent.parent_event_names_from_class(),
        context=context,
    )


def image_urls(event: UserMessageEvent) -> list[str]:
    return [str(block.url) for message in event.messages for block in message.blocks if block.block_type == "image"]


@pytest.mark.asyncio
class TestImagesInMessages:
    async def test_an_image_is_stored_and_referenced_in_its_place(self, context: ApiPayloadContext, s3: FakeS3):
        event = await send({"messages": [image_message(data_url())]}, context)

        [url] = image_urls(event)
        assert url.startswith(FOLDER) and url.endswith(".png")
        assert s3.objects[url.removeprefix("s3://agent-files/")] == base64.b64decode(PNG)
        assert PNG not in event.model_dump_json()

    async def test_an_image_resent_with_the_history_is_stored_once(self, context: ApiPayloadContext, s3: FakeS3):
        await send({"messages": [image_message(data_url())]}, context)
        event = await send({"messages": [image_message(data_url()), image_message(data_url())]}, context)

        assert len(set(image_urls(event))) == 1
        assert s3.puts == 1

    async def test_base64_in_the_image_field_is_stored_too(self, context: ApiPayloadContext, s3: FakeS3):
        block = {"block_type": "image", "image": PNG, "image_mimetype": "image/png"}
        event = await send({"messages": [image_message(block)]}, context)

        assert image_urls(event)[0].startswith(FOLDER)
        assert event.messages[0].blocks[1].image is None

    async def test_web_links_and_own_references_are_kept(self, context: ApiPayloadContext, s3: FakeS3):
        own = f"{FOLDER}{'a' * 64}.png"
        blocks = [{"block_type": "image", "url": "https://example.com/a.png"}, {"block_type": "image", "url": own}]
        event = await send({"messages": [image_message(*blocks)]}, context)

        assert image_urls(event) == ["https://example.com/a.png", own]
        assert s3.puts == 0

    @pytest.mark.parametrize(
        "block",
        [
            {"block_type": "image", "url": f"s3://agent-files/Other/b2/images/{'a' * 64}.png"},
            {"block_type": "image", "url": "s3://agent-files/Universal/a1/some-file-id/report.pdf"},
            {"block_type": "image", "path": "/etc/passwd"},
        ],
    )
    async def test_references_outside_the_agents_images_and_paths_are_refused(
        self, context: ApiPayloadContext, block: dict[str, Any]
    ):
        with pytest.raises(HTTPException) as refused:
            await send({"messages": [image_message(block)]}, context)
        assert refused.value.status_code == 400

    @pytest.mark.parametrize(
        ("block", "status_code"),
        [
            (data_url("not base64!"), 422),
            (data_url(media_type="application/pdf"), 415),
            (data_url(base64.b64encode(b"<svg onload=alert(1)/>").decode(), "image/svg+xml"), 415),
            (data_url(base64.b64encode(b"x" * 64).decode()), 413),
        ],
    )
    async def test_a_bad_image_stores_nothing(
        self,
        context: ApiPayloadContext,
        s3: FakeS3,
        monkeypatch: pytest.MonkeyPatch,
        block: dict[str, Any],
        status_code: int,
    ):
        monkeypatch.setenv("AGENT_INLINE_IMAGE_MAX_BYTES", "32")
        good_file = {"filename": "a.txt", "file_type": "text/plain", "content": base64.b64encode(b"hi").decode()}

        with pytest.raises(HTTPException) as refused:
            await send({"messages": [image_message(data_url(PNG[:8]), block)], "files": [good_file]}, context)

        assert refused.value.status_code == status_code
        assert s3.objects == {}
