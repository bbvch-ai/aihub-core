"""Plain-model calls are capped at the model's output ceiling and explain a blank answer (aihub-incidents#72).

The incident: a direct call to Qwen3.5 sent no `max_tokens`, so the model reasoned until the provider's 204,800-token
window was full, eleven minutes later, and finished on `length` with empty content.
"""

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import httpx
import openai
import pytest
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.testing.auth_utils.test_identity import fake_user

from swiss_ai_hub.api.i18n.api_locale_handler import ApiLocaleHandler
from swiss_ai_hub.api.routes.openai.dto.chat_completion_request import ChatCompletionRequest
from swiss_ai_hub.api.routes.openai.openai_service import OpenaiService

_SERVICE = "swiss_ai_hub.api.routes.openai.openai_service"
_QWEN = "text-generation/Qwen3.5-122B-A10B-FP8"
_CEILING = 32768
_NOTICE_KEY = "api.common.output_budget_exhausted"


def _en() -> ApiLocaleHandler:
    return ApiLocaleHandler(locale="en")


def _request(**limits: int) -> ChatCompletionRequest:
    return ChatCompletionRequest(model=_QWEN, messages=[{"role": "user", "content": "summarise"}], **limits)


def _sent_limits(request: ChatCompletionRequest) -> dict:
    """What `_filter_kwargs` forwards: only the fields set on the request."""
    dumped = request.model_dump(exclude_unset=True)
    return {field: dumped[field] for field in ("max_tokens", "max_completion_tokens") if field in dumped}


class TestOutputLimit:
    def test_defaults_to_the_ceiling_when_the_caller_sets_none(self):
        request = _request()

        OpenaiService._apply_output_limit(request, _CEILING)

        assert _sent_limits(request) == {"max_tokens": _CEILING}

    @pytest.mark.parametrize("field", ["max_tokens", "max_completion_tokens"])
    def test_lowers_a_request_above_the_ceiling(self, field: str):
        request = _request(**{field: 200_000})

        OpenaiService._apply_output_limit(request, _CEILING)

        assert _sent_limits(request) == {field: _CEILING}

    @pytest.mark.parametrize("field", ["max_tokens", "max_completion_tokens"])
    def test_keeps_a_request_below_the_ceiling(self, field: str):
        request = _request(**{field: 512})

        OpenaiService._apply_output_limit(request, _CEILING)

        assert _sent_limits(request) == {field: 512}

    def test_caps_both_fields_when_the_caller_sends_both(self):
        request = _request(max_tokens=100_000, max_completion_tokens=256)

        OpenaiService._apply_output_limit(request, _CEILING)

        assert _sent_limits(request) == {"max_tokens": _CEILING, "max_completion_tokens": 256}


class TestMaxOutputTokens:
    @pytest.mark.asyncio
    async def test_reads_the_named_models_ceiling_from_litellm(self):
        model_info = {
            "data": [
                {"model_name": "text-generation/gemma-4-31B-it", "model_info": {"max_output_tokens": 8192}},
                {"model_name": _QWEN, "model_info": {"max_output_tokens": _CEILING}},
            ]
        }
        listing = Mock(json=lambda: model_info)
        gateway = SimpleNamespace(httpx_aclient=SimpleNamespace(get=AsyncMock(return_value=listing)))

        with patch(f"{_SERVICE}.LiteLLMProxySettings", return_value=gateway):
            assert await OpenaiService._max_output_tokens(_QWEN) == _CEILING


def _chunk(delta: dict, finish_reason: str | None = None) -> dict:
    return {
        "id": "chatcmpl-1",
        "object": "chat.completion.chunk",
        "created": 0,
        "model": _QWEN,
        "choices": [{"index": 0, "delta": delta, "finish_reason": finish_reason}],
    }


def _gateway(captured: list[dict], response: httpx.Response) -> openai.AsyncOpenAI:
    """A real SDK client over a mock transport that records each request body it was sent."""

    def handle(request: httpx.Request) -> httpx.Response:
        captured.append(json.loads(request.content))
        return response

    return openai.AsyncOpenAI(
        api_key="sk-test",
        base_url="http://litellm:4000",
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handle), base_url="http://litellm:4000"),
    )


def _sse(chunks: list[dict]) -> httpx.Response:
    body = "".join(f"data: {json.dumps(chunk)}\n\n" for chunk in chunks) + "data: [DONE]\n\n"
    return httpx.Response(200, headers={"content-type": "text/event-stream"}, content=body)


async def _call(request: ChatCompletionRequest, client: openai.AsyncOpenAI):
    with (
        patch.object(OpenaiService, "get_model", new=AsyncMock()),
        patch.object(OpenaiService, "_assert_model_access", new=Mock()),
        patch.object(OpenaiService, "_max_output_tokens", new=AsyncMock(return_value=_CEILING)),
        patch(f"{_SERVICE}.LiteLLMService.openai_aclient_for_user", new=AsyncMock(return_value=client)),
    ):
        return await OpenaiService.chat_completion(
            model_name=_QWEN, chat_completion_request=request, user=fake_user(), t=_en()
        )


def _streamed_deltas(lines: list[str]) -> list[str | None]:
    *chunks, end = lines
    assert end == OpenaiService.STREAM_END
    return [json.loads(line.removeprefix("data: "))["choices"][0]["delta"].get("content") for line in chunks]


class TestDirectCallsAreCapped:
    @pytest.mark.asyncio
    async def test_a_call_without_a_limit_reaches_the_gateway_with_the_ceiling(self):
        """The incident's request: no `max_tokens` from the caller, so nothing stopped the reasoning."""
        captured: list[dict] = []
        completion = {
            "id": "chatcmpl-1",
            "object": "chat.completion",
            "created": 0,
            "model": _QWEN,
            "choices": [{"index": 0, "message": {"role": "assistant", "content": "Done."}, "finish_reason": "stop"}],
        }

        await _call(_request(), _gateway(captured, httpx.Response(200, json=completion)))

        assert captured[0]["max_tokens"] == _CEILING


class TestBlankAnswersAreExplained:
    @pytest.mark.asyncio
    async def test_a_stream_that_ends_on_length_without_content_gets_the_notice(self):
        captured: list[dict] = []
        reasoning_only = [
            _chunk({"role": "assistant", "content": None, "reasoning_content": "Let me think"}),
            _chunk({"content": None, "reasoning_content": " some more"}, finish_reason="length"),
        ]
        request = _request()
        request.stream = True

        response = await _call(request, _gateway(captured, _sse(reasoning_only)))
        streamed = [line async for line in response.body_iterator]

        assert _streamed_deltas(streamed)[-1] == _en()(_NOTICE_KEY)

    @pytest.mark.asyncio
    async def test_a_stream_cut_off_mid_answer_is_left_as_it_is(self):
        """A partial answer is still something to work with, so it gets no notice appended."""
        captured: list[dict] = []
        cut_off = [_chunk({"role": "assistant", "content": "The contracts"}), _chunk({"content": " cover"}, "length")]
        request = _request()
        request.stream = True

        response = await _call(request, _gateway(captured, _sse(cut_off)))
        streamed = [line async for line in response.body_iterator]

        assert _streamed_deltas(streamed) == ["The contracts", " cover"]

    @pytest.mark.asyncio
    async def test_a_blank_non_streamed_answer_carries_the_notice(self):
        captured: list[dict] = []
        blank = {
            "id": "chatcmpl-1",
            "object": "chat.completion",
            "created": 0,
            "model": _QWEN,
            "choices": [{"index": 0, "message": {"role": "assistant", "content": ""}, "finish_reason": "length"}],
        }

        completion = await _call(_request(), _gateway(captured, httpx.Response(200, json=blank)))

        assert completion.choices[0].message.content == _en()(_NOTICE_KEY)

    @pytest.mark.asyncio
    async def test_a_complete_non_streamed_answer_is_untouched(self):
        captured: list[dict] = []
        answered = {
            "id": "chatcmpl-1",
            "object": "chat.completion",
            "created": 0,
            "model": _QWEN,
            "choices": [{"index": 0, "message": {"role": "assistant", "content": "Done."}, "finish_reason": "stop"}],
        }

        completion = await _call(_request(), _gateway(captured, httpx.Response(200, json=answered)))

        assert completion.choices[0].message.content == "Done."

    @pytest.mark.parametrize("locale", LocaleHandler.LOCALE_WHITE_LIST)
    def test_every_locale_defines_the_notice(self, locale: str):
        notice = ApiLocaleHandler(locale=locale)(_NOTICE_KEY)

        assert notice and notice != _NOTICE_KEY
