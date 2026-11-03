import base64
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException
from swiss_ai_hub.core.events import ApiPayloadContext
from swiss_ai_hub.core.events.agent import UserUploadedFile
from swiss_ai_hub.core.testing.auth_utils.test_identity import fake_user

from swiss_ai_hub.api.routes.openai.dto.chat_completion_request import ChatCompletionRequest
from swiss_ai_hub.api.routes.openai.openai_service import OpenaiService

_SERVICE = "swiss_ai_hub.api.routes.openai.openai_service"
THREAD_ID = "6a0000000000000000000001"
PDF = base64.b64encode(b"%PDF-1.4").decode()
PNG = base64.b64encode(b"\x89PNG").decode()
UPLOADED = {"filename": "old.pdf", "file_type": "application/pdf", "file_id": "550e8400-e29b-41d4-a716-446655440000"}
FILE_PART = {"type": "file", "file": {"filename": "a.pdf", "file_data": PDF}}
IMAGE_PART = {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{PNG}"}}


def request_with(content: list | str, metadata: dict | None = None) -> ChatCompletionRequest:
    return ChatCompletionRequest.model_validate(
        {
            "model": "Agent/a1",
            "messages": [{"role": "user", "content": content}],
            "metadata": {"thread_id": THREAD_ID, **(metadata or {})},
        }
    )


@pytest.fixture
def context() -> ApiPayloadContext:
    return ApiPayloadContext(
        user=fake_user(),
        locale="en",
        agent_class="Agent",
        agent_id="a1",
        thread_id=THREAD_ID,
        s3_client=Mock(),
    )


@pytest.mark.asyncio
async def test_files_and_images_for_a_thread_the_user_may_not_use_are_never_stored(context: ApiPayloadContext):
    request = request_with([FILE_PART, IMAGE_PART])
    store_all = AsyncMock()
    store_images = AsyncMock()
    with (
        patch(
            f"{_SERVICE}.ChatService.existing_thread_of",
            side_effect=HTTPException(status_code=403, detail="User not part of the thread"),
        ),
        patch(f"{_SERVICE}.InlineFile.store_all", store_all),
        patch(f"{_SERVICE}.StoredImage.store_all", store_images),
        pytest.raises(HTTPException) as refused,
    ):
        await OpenaiService._agent_turn(request, context)

    assert refused.value.status_code == 403
    store_all.assert_not_awaited()
    store_images.assert_not_awaited()


@pytest.mark.asyncio
async def test_inline_files_answering_an_open_request_are_refused_before_storing(context: ApiPayloadContext):
    request = request_with([FILE_PART, IMAGE_PART])
    store_all = AsyncMock()
    store_images = AsyncMock()
    with (
        patch(f"{_SERVICE}.ChatService.existing_thread_of", return_value=Mock(id=THREAD_ID)),
        patch(
            f"{_SERVICE}.PersistedAgentEventEntity.open_human_in_the_loop_requests_for_thread", return_value=[Mock()]
        ),
        patch(f"{_SERVICE}.InlineFile.store_all", store_all),
        patch(f"{_SERVICE}.StoredImage.store_all", store_images),
        pytest.raises(HTTPException) as refused,
    ):
        await OpenaiService._agent_turn(request, context)

    assert refused.value.status_code == 409
    store_all.assert_not_awaited()
    store_images.assert_not_awaited()


@pytest.mark.asyncio
async def test_an_answer_to_an_open_request_without_inline_files_goes_through(context: ApiPayloadContext):
    request = request_with("Yes, go ahead.", metadata={"files": [UPLOADED]})
    with (
        patch(f"{_SERVICE}.ChatService.existing_thread_of", return_value=Mock(id=THREAD_ID)),
        patch(
            f"{_SERVICE}.PersistedAgentEventEntity.open_human_in_the_loop_requests_for_thread", return_value=[Mock()]
        ),
    ):
        _, files = await OpenaiService._agent_turn(request, context)

    assert files == [UserUploadedFile(**UPLOADED)]
