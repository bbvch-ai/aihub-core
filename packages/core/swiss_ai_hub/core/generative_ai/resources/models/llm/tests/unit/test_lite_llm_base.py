from collections.abc import Callable, Iterator
from unittest.mock import MagicMock, patch

import httpx
import pytest

from swiss_ai_hub.core.generative_ai.resources.models.llm import lite_llm_base
from swiss_ai_hub.core.generative_ai.resources.models.llm.lite_llm_base import (
    MODEL_INFO_ATTEMPTS,
    _fetch_all_model_info_cached,
)
from swiss_ai_hub.core.generative_ai.resources.models.llm.llm_config import LLMConfig

MODEL_INFO = {"data": [{"model_name": "text-generation/gemma-4-31B-it", "model_info": {"max_input_tokens": 8192}}]}


@pytest.fixture(autouse=True)
def _fresh_model_info_cache(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    _fetch_all_model_info_cached.cache_clear()
    monkeypatch.setattr("time.sleep", lambda _seconds: None)
    yield
    _fetch_all_model_info_cached.cache_clear()


def _serve_model_info(responses: list[Callable[[httpx.Request], httpx.Response]]) -> list[httpx.Request]:
    """Answers each request with the next responder in turn and records the requests it saw."""
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return responses[len(seen) - 1](request)

    proxy_settings = MagicMock()
    proxy_settings.httpx_client = httpx.Client(transport=httpx.MockTransport(handler), base_url="http://litellm:4000")
    patcher = patch.object(lite_llm_base, "LiteLLMProxySettings", return_value=proxy_settings)
    patcher.start()
    return seen


@pytest.fixture(autouse=True)
def _stop_patches() -> Iterator[None]:
    yield
    patch.stopall()


def _read_timeout(request: httpx.Request) -> httpx.Response:
    raise httpx.ReadTimeout("timed out", request=request)


def _ok(_request: httpx.Request) -> httpx.Response:
    return httpx.Response(200, json=MODEL_INFO)


def _status(code: int) -> Callable[[httpx.Request], httpx.Response]:
    return lambda _request: httpx.Response(code, json={"error": "x"})


def test_model_info_waits_longer_than_the_httpx_default():
    seen = _serve_model_info([_ok])

    assert _fetch_all_model_info_cached() == MODEL_INFO
    assert seen[0].extensions["timeout"]["read"] == 30.0


def test_model_info_retries_a_read_timeout_until_litellm_answers():
    seen = _serve_model_info([_read_timeout, _read_timeout, _ok])

    assert _fetch_all_model_info_cached() == MODEL_INFO
    assert len(seen) == 3


def test_model_info_retries_a_server_error():
    seen = _serve_model_info([_status(503), _ok])

    assert _fetch_all_model_info_cached() == MODEL_INFO
    assert len(seen) == 2


def test_model_info_fails_at_once_on_a_client_error():
    seen = _serve_model_info([_status(401), _ok])

    with pytest.raises(httpx.HTTPStatusError):
        _fetch_all_model_info_cached()
    assert len(seen) == 1


def test_model_info_gives_up_after_the_last_attempt():
    seen = _serve_model_info([_read_timeout] * MODEL_INFO_ATTEMPTS)

    with pytest.raises(httpx.ReadTimeout):
        _fetch_all_model_info_cached()
    assert len(seen) == MODEL_INFO_ATTEMPTS


def test_model_info_is_fetched_once_per_process():
    seen = _serve_model_info([_ok, _ok])

    LLMConfig(model_name="text-generation/gemma-4-31B-it").get_model_info()
    LLMConfig(model_name="text-generation/gemma-4-31B-it").get_model_info()

    assert len(seen) == 1


def _deny_network(*_args: object, **_kwargs: object) -> None:
    raise AssertionError("token_counter must not perform network I/O")


def test_token_counter_tokenizes_locally_without_network():
    config = LLMConfig(model_name="text-generation/gemma-4-31B-it")

    with patch(
        "swiss_ai_hub.core.generative_ai.resources.models.llm.lite_llm_base.LiteLLMProxySettings",
        side_effect=_deny_network,
    ):
        tokens = config.token_counter("hello world")

    assert tokens == config.token_counter("hello world")
    assert len(tokens) > 0


def test_token_counter_is_stable_across_property_accesses():
    config = LLMConfig(model_name="text-generation/gemma-4-31B-it")

    first_access = config.token_counter
    second_access = config.token_counter

    assert first_access("The quick brown fox.") == second_access("The quick brown fox.")
