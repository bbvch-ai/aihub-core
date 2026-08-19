import json
from unittest.mock import AsyncMock, Mock, patch

import httpx
import openai
import pytest
from swiss_ai_hub.core.i18n import LocaleHandler
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
        lambda _request: httpx.Response(200, headers={"content-type": "text/event-stream"}, content=_sse_body(contents))
    )
    return openai.AsyncOpenAI(
        api_key="sk-test",
        base_url="http://litellm:4000",
        http_client=httpx.AsyncClient(transport=transport, base_url="http://litellm:4000"),
    )


def _rejecting_client(status_code: int) -> openai.AsyncOpenAI:
    """Same wiring as `_streaming_client`, except the gateway rejects the request outright."""
    transport = httpx.MockTransport(
        lambda _request: httpx.Response(status_code, json={"error": {"message": "Invalid model name"}})
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
            model_name=_MODEL, chat_completion_request=request, user=fake_user(), t=LocaleHandler(locale="en")
        )

    streamed = [chunk async for chunk in response.body_iterator]

    assert _streamed_contents(streamed) == ["Hello", " world"]
    assert not client.is_closed()

    # The only happy path through `chat_completion` in the suite, so it is the only place the identity
    # injection's call site can be pinned: every test in test_openai_model_identity_unit_tests.py either
    # calls `_apply_model_identity` directly or asserts it did *not* run, so deleting the call from
    # `chat_completion` would otherwise leave the suite green and silently reopen issue #144.
    assert request.messages[0]["role"] == "system"
    assert "gemma-4-31B-it" in request.messages[0]["content"]


@pytest.mark.asyncio
async def test_streaming_upstream_rejection_surfaces_in_the_handler_scope() -> None:
    """
    The stream is opened by `chat_completion` itself, not by the generator Starlette drains later, so a
    gateway rejection still reaches `ModelGatewayErrorHandler` and can be answered with a body that names
    the cause. Issued from inside the generator it would instead truncate an already-started response,
    leaving the caller with a dead stream and no message.
    """
    client = _rejecting_client(400)
    request = ChatCompletionRequest(model=_MODEL, messages=[{"role": "user", "content": "hi"}], stream=True)

    with (
        patch.object(OpenaiService, "get_model", new=AsyncMock()),
        patch.object(OpenaiService, "_assert_model_access", new=Mock()),
        patch(f"{_SERVICE}.LiteLLMService.openai_aclient_for_user", new=AsyncMock(return_value=client)),
    ):
        with pytest.raises(openai.APIStatusError):
            await OpenaiService.chat_completion(
                model_name=_MODEL, chat_completion_request=request, user=fake_user(), t=LocaleHandler(locale="en")
            )
