"""Every agent model call names the acting tenant as its LiteLLM customer (ADR 2026_11_09)."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from swiss_ai_hub.core.auth.identity.tenant_identity import TenantIdentity
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.generative_ai.resources.models.llm.llm_config import LLMConfig
from swiss_ai_hub.core.generative_ai.resources.models.llm.reranking_model_config import RerankingModelConfig
from swiss_ai_hub.core.infrastructure.litellm.lite_llm_customer_service import LiteLLMCustomerService
from swiss_ai_hub.core.infrastructure.litellm.lite_llm_service import LiteLLMService

pytestmark = pytest.mark.unit

HEADER = LiteLLMCustomerService.CUSTOMER_HEADER
TENANT = TenantIdentity(id="tenant-a", name="Tenant A", access_rules=[])
USER = UserIdentity(id="user-1", name="Ada", email="ada@example.com", roles=[], acting_within_tenant=TENANT)


async def _headers_sent_by_cost_reporting_llm(user: UserIdentity | None, extra_headers: dict[str, str]) -> dict:
    config = LLMConfig(model_name="text-generation/gemma-4-31B-it")
    llm = MagicMock(aclose=AsyncMock())
    with (
        patch.object(LLMConfig, "to_llama_index", return_value=(llm, MagicMock())) as to_llama_index,
        patch.object(LiteLLMService, "api_key_for_user", new=AsyncMock(return_value="sk-user")),
        patch.dict(LiteLLMCustomerService._aliases, {TENANT.id: TENANT.name}),
    ):
        async with config.cost_reporting_llm(displayer=AsyncMock(), extra_headers=extra_headers, user=user):
            pass
    return to_llama_index.call_args.kwargs["extra_headers"]


@pytest.mark.asyncio
async def test_an_agent_call_names_the_acting_tenant_next_to_the_callers_headers() -> None:
    headers = await _headers_sent_by_cost_reporting_llm(USER, {"x-litellm-enable-message-redaction": "true"})

    assert headers == {"x-litellm-enable-message-redaction": "true", HEADER: "tenant-a"}


@pytest.mark.asyncio
async def test_a_run_without_a_user_names_the_no_tenant_customer() -> None:
    """Scheduled and delegated runs carry no user, and the caller's headers must not name a tenant for them."""
    headers = await _headers_sent_by_cost_reporting_llm(None, {HEADER: "spoofed"})

    assert headers == {HEADER: LiteLLMCustomerService.NO_TENANT_CUSTOMER_ID}


def test_a_rerank_sends_the_customer_header(monkeypatch: pytest.MonkeyPatch) -> None:
    """Cohere's client takes no headers, so this pins that the ones set on it reach the request."""
    monkeypatch.setenv("LITE_LLM_PROXY_BASE_URL", "http://litellm")
    monkeypatch.setenv("LITE_LLM_PROXY_API_KEY", "test")
    seen: list[httpx.Request] = []

    def answer(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"id": "r1", "results": [], "meta": {}})

    model_info = {"model_info": {"input_cost_per_token": 0.0, "output_cost_per_token": 0.0}}
    with patch.object(RerankingModelConfig, "get_model_info", return_value=model_info):
        reranker, _ = RerankingModelConfig(model_name="reranker/bge").to_llama_index(extra_headers={HEADER: "tenant-a"})
    reranker._client._client_wrapper.httpx_client.httpx_client = httpx.Client(transport=httpx.MockTransport(answer))

    reranker._client.rerank(model="reranker/bge", query="q", documents=["d"])

    assert seen[0].headers[HEADER] == "tenant-a"
