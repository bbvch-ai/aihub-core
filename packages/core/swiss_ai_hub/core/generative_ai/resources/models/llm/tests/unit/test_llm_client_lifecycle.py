"""Per-call LLM and embedding clients are closed by their owner and fail fast on connect (aihub-core-private#349).

Left to the garbage collector, the OpenAI SDK's finalizer closes a client on the event loop after its sockets are gone;
a new connection reusing a socket's number meanwhile loses its event-loop watch and hangs for the whole request
timeout. A bounded connect turns any remaining hang into a fast retry.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from swiss_ai_hub.core.generative_ai.resources.models.llm.llm_config import LLMConfig, LLMParameter
from swiss_ai_hub.core.generative_ai.resources.models.llm.reranking_model_config import (
    RERANK_TIMEOUT_SECONDS,
    RerankingModelConfig,
)
from swiss_ai_hub.core.generative_ai.resources.models.llm.resilient_open_ai_like import ResilientOpenAILike
from swiss_ai_hub.core.generative_ai.resources.models.llm.resilient_open_ai_like_embedding import (
    ResilientOpenAILikeEmbedding,
)
from swiss_ai_hub.core.infrastructure.litellm.lite_llm_proxy_settings import LiteLLMProxySettings

MODEL_INFO = {"model_info": {"input_cost_per_token": 0.0, "output_cost_per_token": 0.0}}


def _llm() -> ResilientOpenAILike:
    return ResilientOpenAILike(
        model="text-generation/gemma-4-31B-it",
        api_base="http://litellm/v1",
        api_key="test",
        timeout=300.0,
        connect_timeout=5.0,
    )


def _embedding() -> ResilientOpenAILikeEmbedding:
    return ResilientOpenAILikeEmbedding(
        model_name="embedding/bge-m3",
        api_base="http://litellm/v1",
        api_key="test",
        timeout=60.0,
        connect_timeout=5.0,
    )


async def _use_llm(llm: ResilientOpenAILike, *, fail: bool) -> None:
    """Enter `cost_reporting_llm` with `llm` and open its async client, as a real call would."""
    config = LLMConfig(model_name="text-generation/gemma-4-31B-it")
    with patch.object(LLMConfig, "to_llama_index", return_value=(llm, MagicMock())):
        async with config.cost_reporting_llm(displayer=_displayer()) as yielded:
            yielded._get_aclient()
            if fail:
                raise RuntimeError("call failed")


def _displayer() -> AsyncMock:
    return AsyncMock()


class TestClientsAreClosed:
    @pytest.mark.asyncio
    async def test_cost_reporting_llm_closes_the_async_client(self):
        llm = _llm()

        await _use_llm(llm, fail=False)

        assert llm._aclient.is_closed()

    @pytest.mark.asyncio
    async def test_cost_reporting_llm_closes_the_async_client_when_the_block_raises(self):
        llm = _llm()

        with pytest.raises(RuntimeError, match="call failed"):
            await _use_llm(llm, fail=True)

        assert llm._aclient.is_closed()

    @pytest.mark.asyncio
    async def test_cost_reporting_llm_reports_costs_when_the_block_raises(self):
        config = LLMConfig(model_name="text-generation/gemma-4-31B-it")
        cost_tracker = MagicMock()
        displayer = _displayer()

        with (
            patch.object(LLMConfig, "to_llama_index", return_value=(_llm(), cost_tracker)),
            pytest.raises(RuntimeError),
        ):
            async with config.cost_reporting_llm(displayer=displayer):
                raise RuntimeError("call failed")

        displayer.display_llm_costs.assert_awaited_once_with(config.model_name, cost_tracker, None)

    @pytest.mark.asyncio
    async def test_cost_reporting_llm_closes_the_client_when_cost_reporting_fails(self):
        config = LLMConfig(model_name="text-generation/gemma-4-31B-it")
        llm = _llm()
        displayer = _displayer()
        displayer.display_llm_costs.side_effect = RuntimeError("NATS down")

        with (
            patch.object(LLMConfig, "to_llama_index", return_value=(llm, MagicMock())),
            pytest.raises(RuntimeError, match="NATS down"),
        ):
            async with config.cost_reporting_llm(displayer=displayer) as yielded:
                yielded._get_aclient()

        assert llm._aclient.is_closed()

    @pytest.mark.asyncio
    async def test_embedding_aclose_closes_the_async_client(self):
        embedding = _embedding()
        client = embedding._get_aclient()

        await embedding.aclose()

        assert client.is_closed()

    @pytest.mark.asyncio
    async def test_aclose_without_any_call_opens_nothing(self):
        llm = _llm()

        await llm.aclose()

        assert llm._aclient is None
        assert llm._client is None


class TestConnectIsBounded:
    def test_llm_client_connect_timeout_is_separate_from_the_request_timeout(self):
        timeout = _llm()._get_aclient().timeout

        assert timeout == httpx.Timeout(300.0, connect=5.0)

    def test_embedding_client_connect_timeout_is_separate_from_the_request_timeout(self):
        timeout = _embedding()._get_aclient().timeout

        assert timeout == httpx.Timeout(60.0, connect=5.0)

    def test_connect_timeout_is_read_from_the_environment(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("LITE_LLM_PROXY_BASE_URL", "http://litellm")
        monkeypatch.setenv("LITE_LLM_PROXY_CONNECT_TIMEOUT_SECONDS", "2.5")

        assert LiteLLMProxySettings().CONNECT_TIMEOUT_SECONDS == 2.5

    def test_llm_config_passes_the_configured_connect_timeout(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("LITE_LLM_PROXY_BASE_URL", "http://litellm")
        monkeypatch.setenv("LITE_LLM_PROXY_API_KEY", "test")
        monkeypatch.setenv("LITE_LLM_PROXY_CONNECT_TIMEOUT_SECONDS", "2.5")
        model_info = {
            "model_info": {
                **MODEL_INFO["model_info"],
                "max_input_tokens": 8192,
                "mode": "chat",
                "supports_function_calling": False,
                "max_output_tokens": 1024,
            }
        }

        with patch.object(LLMConfig, "get_model_info", return_value=model_info):
            llm, _ = LLMConfig(model_name="text-generation/gemma-4-31B-it").to_llama_index()

        assert llm.connect_timeout == 2.5


class TestTimeouts:
    def test_llm_request_timeout_defaults_to_five_minutes(self):
        assert LLMParameter().timeout == 300.0

    def test_reranker_client_is_bounded(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("LITE_LLM_PROXY_BASE_URL", "http://litellm")
        monkeypatch.setenv("LITE_LLM_PROXY_API_KEY", "test")

        with patch.object(RerankingModelConfig, "get_model_info", return_value=MODEL_INFO):
            reranker, _ = RerankingModelConfig(model_name="reranker/bge").to_llama_index()

        assert reranker._client._client_wrapper.get_timeout() == RERANK_TIMEOUT_SECONDS
