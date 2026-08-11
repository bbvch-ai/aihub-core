import json
from unittest.mock import AsyncMock, Mock, patch

import httpx
import openai
import pytest
from swiss_ai_hub.core.testing.auth_utils.test_identity import fake_user

from swiss_ai_hub.api.routes.openai.dto.chat_completion_request import ChatCompletionRequest
from swiss_ai_hub.api.routes.openai.openai_service import OpenaiService

_SERVICE = "swiss_ai_hub.api.routes.openai.openai_service"
_MODEL = "text-generation/gemma-4-31B-it"


def _sse_body(contents: list[str]) -> str:
    chunks = [
        {
            "id": "chatcmpl-1",
            "object": "chat.completion.chunk",
            "created": 0,
            "model": _MODEL,
            "choices": [{"index": 0, "delta": {"content": content}, "finish_reason": None}],
        }
        for content in contents
    ]
    return "".join(f"data: {json.dumps(chunk)}\n\n" for chunk in chunks) + "data: [DONE]\n\n"


def _streaming_client(contents: list[str]) -> openai.AsyncOpenAI:
    """A real SDK client over a mock transport, so closing it fails the way a closed pooled client would."""
    transport = httpx.MockTransport(
        lambda _request: httpx.Response(
            200, headers={"content-type": "text/event-stream"}, content=_sse_body(contents)
        )
    )
    return openai.AsyncOpenAI(
        api_key="sk-test",
        base_url="http://litellm:4000",
        http_client=httpx.AsyncClient(transport=transport, base_url="http://litellm:4000"),
    )


def _streamed_contents(response) -> list[str]:
    return [json.loads(chunk.removeprefix("data: "))["choices"][0]["delta"]["content"] for chunk in response]


@pytest.mark.asyncio
async def test_streaming_response_outlives_the_handler() -> None:
    """
    `chat_completion` returns a `StreamingResponse` whose generator Starlette only drains after the handler
    has returned, and that generator both issues the request and reads it off the captured client.

    So the client must outlive the handler, which is what forbids scoping it with `async with` and justifies
    the shared pooled client. Draining outside the `with` block below is the point of the test, not tidiness.
    """
    client = _streaming_client(["Hello", " world"])
    request = ChatCompletionRequest(model=_MODEL, messages=[{"role": "user", "content": "hi"}], stream=True)

    with (
        patch.object(OpenaiService, "get_model", new=AsyncMock()),
        patch.object(OpenaiService, "_assert_model_access", new=Mock()),
        patch(f"{_SERVICE}.LiteLLMService.openai_aclient_for_user", new=AsyncMock(return_value=client)),
    ):
        response = await OpenaiService.chat_completion(
            model_name=_MODEL, chat_completion_request=request, user=fake_user(), t=Mock(locale="en")
        )

    streamed = [chunk async for chunk in response.body_iterator]

    assert _streamed_contents(streamed) == ["Hello", " world"]
    assert not client.is_closed()
