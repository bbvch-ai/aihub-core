import functools
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


@pytest.mark.asyncio
async def test_abandoned_stream_is_closed_when_the_consumer_stops_early() -> None:
    """
    A browser tab closed mid-answer makes Starlette call `aclose()` on the body iterator, which raises
    `GeneratorExit` at the `yield`. Opening the stream in the handler's scope is what lets an upstream
    rejection be converted, but it also means an abandoned response has a live httpx stream attached —
    and `with_options()` hands every user a copy over one shared pool, so a leak there is everyone's.

    The `async with` inside the generator is what closes it. Not covered here, because nothing can
    cover it: a generator that is never started at all runs no code on `aclose()`.
    """
    client = _streaming_client(["Hello", " world", " again"])
    request = ChatCompletionRequest(model=_MODEL, messages=[{"role": "user", "content": "hi"}], stream=True)

    # The stream is created inside the handler and only the generator closes over it, so it has to be
    # captured on the way out to be asserted on at all.
    opened: list[openai.AsyncStream] = []
    real_create = client.chat.completions.create

    # functools.wraps so `_filter_kwargs` still sees the real signature — it filters by it, and an
    # untyped **kwargs wrapper makes it drop every argument.
    @functools.wraps(real_create)
    async def capturing_create(**kwargs):
        stream = await real_create(**kwargs)
        opened.append(stream)
        return stream

    with (
        patch.object(OpenaiService, "get_model", new=AsyncMock()),
        patch.object(OpenaiService, "_assert_model_access", new=Mock()),
        patch(f"{_SERVICE}.LiteLLMService.openai_aclient_for_user", new=AsyncMock(return_value=client)),
        patch.object(client.chat.completions, "create", new=capturing_create),
    ):
        response = await OpenaiService.chat_completion(
            model_name=_MODEL, chat_completion_request=request, user=fake_user(), t=LocaleHandler(locale="en")
        )

    iterator = response.body_iterator
    assert await anext(iterator)

    # Asserted on the close call rather than on `response.is_closed`: httpx.MockTransport buffers the
    # body, so the response reads as closed after the first chunk whether or not anything closed it.
    stream = opened[0]
    closes: list[bool] = []
    real_close = stream.close

    async def spy_close() -> None:
        closes.append(True)
        await real_close()

    stream.close = spy_close

    assert closes == []

    await iterator.aclose()

    assert closes == [True], "abandoning the response must close the upstream stream"
    # The stream, not the client: the pooled client stays open for everyone else by design.
    assert client.is_closed() is False
