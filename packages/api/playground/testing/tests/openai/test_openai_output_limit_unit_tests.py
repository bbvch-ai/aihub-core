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
# Infomaniak's 400 for a request whose input + max_tokens exceeds the window, as LiteLLM passes it on.
_WINDOW_REJECTION = {
    "error": {
        "message": "litellm.BadRequestError: OpenAIException - This model's maximum context length is 204800 tokens. "
        "However, you requested 32768 output tokens and your prompt contains at least 180000 input tokens"
    }
}
_JSON_SCHEMA = {"type": "json_schema", "json_schema": {"name": "title", "schema": {"type": "object"}}}


def _en() -> ApiLocaleHandler:
    return ApiLocaleHandler(locale="en")


def _request(stream: bool = False, **fields) -> ChatCompletionRequest:
    return ChatCompletionRequest(
        model=_QWEN, messages=[{"role": "user", "content": "summarise"}], stream=stream, **fields
    )


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

    @pytest.mark.parametrize("caller_limit", [{}, {"max_tokens": 1000}])
    def test_a_model_without_a_ceiling_is_left_alone(self, caller_limit: dict):
        """A model added through LiteLLM's UI may declare no `max_output_tokens`; that must not fail the call."""
        request = _request(**caller_limit)

        OpenaiService._apply_output_limit(request, None)

        assert _sent_limits(request) == caller_limit


def _litellm_listing(models: list[dict]) -> SimpleNamespace:
    listing = Mock(json=lambda: {"data": models})
    return SimpleNamespace(httpx_aclient=SimpleNamespace(get=AsyncMock(return_value=listing)))


class TestMaxOutputTokens:
    @pytest.mark.asyncio
    async def test_reads_the_named_models_ceiling_from_litellm(self):
        gateway = _litellm_listing(
            [
                {"model_name": "text-generation/gemma-4-31B-it", "model_info": {"max_output_tokens": 8192}},
                {"model_name": _QWEN, "model_info": {"max_output_tokens": _CEILING}},
            ]
        )

        with patch(f"{_SERVICE}.LiteLLMProxySettings", return_value=gateway):
            assert await OpenaiService._max_output_tokens(_QWEN) == _CEILING

    @pytest.mark.parametrize(
        "models",
        [
            [{"model_name": _QWEN, "model_info": {"max_output_tokens": None}}],
            [{"model_name": _QWEN, "model_info": {"mode": "chat"}}],
            [{"model_name": "text-generation/gemma-4-31B-it", "model_info": {"max_output_tokens": 8192}}],
        ],
        ids=["declared-as-null", "not-declared", "model-not-listed"],
    )
    @pytest.mark.asyncio
    async def test_reports_no_ceiling_instead_of_failing(self, models: list[dict]):
        with patch(f"{_SERVICE}.LiteLLMProxySettings", return_value=_litellm_listing(models)):
            assert await OpenaiService._max_output_tokens(_QWEN) is None


def _chunk(delta: dict, finish_reason: str | None = None) -> dict:
    return {
        "id": "chatcmpl-1",
        "object": "chat.completion.chunk",
        "created": 0,
        "model": _QWEN,
        "choices": [{"index": 0, "delta": delta, "finish_reason": finish_reason}],
    }


def _completion(content: str, finish_reason: str) -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "id": "chatcmpl-1",
            "object": "chat.completion",
            "created": 0,
            "model": _QWEN,
            "choices": [
                {"index": 0, "message": {"role": "assistant", "content": content}, "finish_reason": finish_reason}
            ],
        },
    )


def _sse(chunks: list[dict]) -> httpx.Response:
    body = "".join(f"data: {json.dumps(chunk)}\n\n" for chunk in chunks) + "data: [DONE]\n\n"
    return httpx.Response(200, headers={"content-type": "text/event-stream"}, content=body)


def _gateway(captured: list[dict], *responses: httpx.Response) -> openai.AsyncOpenAI:
    """A real SDK client over a mock transport that records each request body and answers them in turn."""
    pending = list(responses)

    def handle(request: httpx.Request) -> httpx.Response:
        captured.append(json.loads(request.content))
        return pending.pop(0)

    return openai.AsyncOpenAI(
        api_key="sk-test",
        base_url="http://litellm:4000",
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handle), base_url="http://litellm:4000"),
    )


async def _call(request: ChatCompletionRequest, client: openai.AsyncOpenAI, ceiling: int | None = _CEILING):
    with (
        patch.object(OpenaiService, "get_model", new=AsyncMock()),
        patch.object(OpenaiService, "_assert_model_access", new=Mock()),
        patch.object(OpenaiService, "_max_output_tokens", new=AsyncMock(return_value=ceiling)),
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

        await _call(_request(), _gateway(captured, _completion("Done.", "stop")))

        assert captured[0]["max_tokens"] == _CEILING

    @pytest.mark.asyncio
    async def test_a_model_without_a_ceiling_is_called_as_before(self):
        captured: list[dict] = []

        await _call(_request(), _gateway(captured, _completion("Done.", "stop")), ceiling=None)

        assert "max_tokens" not in captured[0]


class TestLongChatsStillFitTheWindow:
    """Input and output share one window, and a chat past `max_input_tokens` leaves less room than the ceiling.
    Before the default limit existed such a chat worked with whatever room was left, so it must keep working."""

    @pytest.mark.parametrize("stream", [False, True])
    @pytest.mark.asyncio
    async def test_a_window_rejection_is_retried_without_the_default_limit(self, stream: bool):
        captured: list[dict] = []
        answer = _sse([_chunk({"content": "Done."}, "stop")]) if stream else _completion("Done.", "stop")

        await _call(_request(stream=stream), _gateway(captured, httpx.Response(400, json=_WINDOW_REJECTION), answer))

        assert captured[0]["max_tokens"] == _CEILING
        assert "max_tokens" not in captured[1]

    @pytest.mark.asyncio
    async def test_a_callers_own_limit_is_not_dropped(self):
        """The caller chose that limit, and before this change the same request was rejected the same way."""
        captured: list[dict] = []

        with pytest.raises(openai.BadRequestError):
            await _call(_request(max_tokens=1000), _gateway(captured, httpx.Response(400, json=_WINDOW_REJECTION)))

        assert len(captured) == 1

    @pytest.mark.asyncio
    async def test_other_rejections_are_not_retried(self):
        captured: list[dict] = []
        unknown_model = httpx.Response(400, json={"error": {"message": "Invalid model name"}})

        with pytest.raises(openai.BadRequestError):
            await _call(_request(), _gateway(captured, unknown_model))

        assert len(captured) == 1


class TestBlankAnswersAreExplained:
    @pytest.mark.asyncio
    async def test_a_stream_that_ends_on_length_without_content_gets_the_notice(self):
        captured: list[dict] = []
        reasoning_only = [
            _chunk({"role": "assistant", "content": None, "reasoning_content": "Let me think"}),
            _chunk({"content": None, "reasoning_content": " some more"}, finish_reason="length"),
        ]

        response = await _call(_request(stream=True), _gateway(captured, _sse(reasoning_only)))
        streamed = [line async for line in response.body_iterator]

        assert _streamed_deltas(streamed)[-1] == _en()(_NOTICE_KEY)

    @pytest.mark.asyncio
    async def test_a_stream_cut_off_mid_answer_is_left_as_it_is(self):
        """A partial answer is still something to work with, so it gets no notice appended."""
        captured: list[dict] = []
        cut_off = [_chunk({"role": "assistant", "content": "The contracts"}), _chunk({"content": " cover"}, "length")]

        response = await _call(_request(stream=True), _gateway(captured, _sse(cut_off)))
        streamed = [line async for line in response.body_iterator]

        assert _streamed_deltas(streamed) == ["The contracts", " cover"]

    @pytest.mark.asyncio
    async def test_a_blank_non_streamed_answer_carries_the_notice(self):
        captured: list[dict] = []

        completion = await _call(_request(), _gateway(captured, _completion("", "length")))

        assert completion.choices[0].message.content == _en()(_NOTICE_KEY)

    @pytest.mark.asyncio
    async def test_a_complete_non_streamed_answer_is_untouched(self):
        captured: list[dict] = []

        completion = await _call(_request(), _gateway(captured, _completion("Done.", "stop")))

        assert completion.choices[0].message.content == "Done."

    @pytest.mark.parametrize(
        "fields",
        [{"max_tokens": 20}, {"response_format": _JSON_SCHEMA}],
        ids=["caller-set-a-limit", "caller-asked-for-json"],
    )
    @pytest.mark.asyncio
    async def test_a_caller_expecting_a_short_or_structured_answer_gets_no_prose(self, fields: dict):
        """A title generator or a JSON caller would take the notice as its answer: an empty one is what it handles."""
        captured: list[dict] = []

        completion = await _call(_request(**fields), _gateway(captured, _completion("", "length")))

        assert completion.choices[0].message.content == ""

    @pytest.mark.asyncio
    async def test_a_stream_with_tools_gets_no_notice(self):
        captured: list[dict] = []
        tool = {"type": "function", "function": {"name": "lookup", "parameters": {"type": "object"}}}
        reasoning_only = [_chunk({"role": "assistant", "content": None, "reasoning_content": "hmm"}, "length")]

        response = await _call(_request(stream=True, tools=[tool]), _gateway(captured, _sse(reasoning_only)))
        streamed = [line async for line in response.body_iterator]

        assert _streamed_deltas(streamed) == [None]

    @pytest.mark.parametrize("locale", LocaleHandler.LOCALE_WHITE_LIST)
    def test_every_locale_defines_the_notice(self, locale: str):
        notice = ApiLocaleHandler(locale=locale)(_NOTICE_KEY)

        assert notice and notice != _NOTICE_KEY
