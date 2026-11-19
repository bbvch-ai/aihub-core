import logging
from collections.abc import Callable, Iterator
from unittest.mock import MagicMock, patch

import httpx
import pytest

from swiss_ai_hub.core.generative_ai.resources.models.llm import lite_llm_model_info
from swiss_ai_hub.core.generative_ai.resources.models.llm.lite_llm_model_info import LiteLLMModelInfo
from swiss_ai_hub.core.generative_ai.resources.models.llm.llm_config import LLMConfig

MODEL_INFO = {"data": [{"model_name": "text-generation/gemma-4-31B-it", "model_info": {"max_input_tokens": 8192}}]}

Responder = Callable[[httpx.Request], httpx.Response]


@pytest.fixture(autouse=True)
def _fresh_process(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setattr(LiteLLMModelInfo, "_all_models", None)
    monkeypatch.setattr(LiteLLMModelInfo, "_patient", False)
    monkeypatch.setattr("time.sleep", lambda _seconds: None)
    yield
    patch.stopall()


def _serve_model_info(responses: list[Responder]) -> list[httpx.Request]:
    """Answers each request with the next responder in turn and records the requests it saw."""
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return responses[len(seen) - 1](request)

    proxy_settings = MagicMock()
    proxy_settings.httpx_client = httpx.Client(transport=httpx.MockTransport(handler), base_url="http://litellm:4000")
    patch.object(lite_llm_model_info, "LiteLLMProxySettings", return_value=proxy_settings).start()
    return seen


def _read_timeout(request: httpx.Request) -> httpx.Response:
    raise httpx.ReadTimeout("timed out", request=request)


def _ok(_request: httpx.Request) -> httpx.Response:
    return httpx.Response(200, json=MODEL_INFO)


def _status(code: int) -> Responder:
    return lambda _request: httpx.Response(code, json={"error": "x"})


def test_request_paths_get_a_short_lookup():
    seen = _serve_model_info([_read_timeout] * LiteLLMModelInfo.QUICK_ATTEMPTS)

    with pytest.raises(httpx.ReadTimeout):
        LiteLLMModelInfo.all_models()
    assert len(seen) == LiteLLMModelInfo.QUICK_ATTEMPTS
    assert seen[0].extensions["timeout"]["read"] == LiteLLMModelInfo.QUICK_READ_TIMEOUT_SECONDS


def test_a_patient_process_waits_longer_and_retries_more():
    LiteLLMModelInfo.wait_patiently()
    seen = _serve_model_info([_read_timeout] * (LiteLLMModelInfo.PATIENT_ATTEMPTS - 1) + [_ok])

    assert LiteLLMModelInfo.all_models() == MODEL_INFO
    assert len(seen) == LiteLLMModelInfo.PATIENT_ATTEMPTS
    assert seen[0].extensions["timeout"]["read"] == LiteLLMModelInfo.PATIENT_READ_TIMEOUT_SECONDS


def test_a_patient_process_gives_up_after_its_last_attempt():
    LiteLLMModelInfo.wait_patiently()
    seen = _serve_model_info([_read_timeout] * LiteLLMModelInfo.PATIENT_ATTEMPTS)

    with pytest.raises(httpx.ReadTimeout):
        LiteLLMModelInfo.all_models()
    assert len(seen) == LiteLLMModelInfo.PATIENT_ATTEMPTS


def test_a_server_error_is_retried():
    seen = _serve_model_info([_status(503), _ok])

    assert LiteLLMModelInfo.all_models() == MODEL_INFO
    assert len(seen) == 2


def test_a_client_error_fails_at_once():
    seen = _serve_model_info([_status(401), _ok])

    with pytest.raises(httpx.HTTPStatusError):
        LiteLLMModelInfo.all_models()
    assert len(seen) == 1


def test_each_retry_is_logged(caplog: pytest.LogCaptureFixture):
    _serve_model_info([_read_timeout, _ok])

    with caplog.at_level(logging.WARNING, logger=lite_llm_model_info.__name__):
        LiteLLMModelInfo.all_models()

    assert any("Retrying" in record.getMessage() for record in caplog.records)


def test_a_failed_lookup_is_not_remembered():
    seen = _serve_model_info([_status(401), _ok])

    with pytest.raises(httpx.HTTPStatusError):
        LiteLLMModelInfo.all_models()
    assert LiteLLMModelInfo.all_models() == MODEL_INFO
    assert len(seen) == 2


def test_model_info_is_fetched_once_per_process():
    seen = _serve_model_info([_ok, _ok])

    LLMConfig(model_name="text-generation/gemma-4-31B-it").get_model_info()
    LLMConfig(model_name="text-generation/gemma-4-31B-it").get_model_info()

    assert len(seen) == 1
