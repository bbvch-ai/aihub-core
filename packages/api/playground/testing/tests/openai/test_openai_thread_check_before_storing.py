import base64
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException
from swiss_ai_hub.core.events import ApiPayloadContext
from swiss_ai_hub.core.testing.auth_utils.test_identity import fake_user

from swiss_ai_hub.api.routes.openai.dto.chat_completion_request import ChatCompletionRequest
from swiss_ai_hub.api.routes.openai.openai_service import OpenaiService

_SERVICE = "swiss_ai_hub.api.routes.openai.openai_service"
PDF = base64.b64encode(b"%PDF-1.4").decode()
PNG = base64.b64encode(b"\x89PNG").decode()


@pytest.mark.asyncio
async def test_files_and_images_for_a_thread_the_user_may_not_use_are_never_stored():
    request = ChatCompletionRequest.model_validate(
        {
            "model": "Agent/a1",
            "metadata": {"thread_id": "6a0000000000000000000001"},
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "file", "file": {"filename": "a.pdf", "file_data": PDF}},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{PNG}"}},
                    ],
                }
            ],
        }
    )
    context = ApiPayloadContext(
        user=fake_user(),
        locale="en",
        agent_class="Agent",
        agent_id="a1",
        thread_id="6a0000000000000000000001",
        s3_client=Mock(),
    )
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
