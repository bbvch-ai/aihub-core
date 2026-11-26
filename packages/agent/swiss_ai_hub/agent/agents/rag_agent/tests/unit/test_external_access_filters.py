"""An external system decides per asking user which documents a RAG agent retrieves; any failure means nothing."""

import asyncio

import httpx
import pytest
from swiss_ai_hub.core.generative_ai import (
    EmbeddingModelConfig,
    KnowledgeRetrieverConfig,
    MetadataFilterPair,
    RetrievalRuntimeConfig,
)
from swiss_ai_hub.core.persistence import MilvusVectorStoreConfig
from swiss_ai_hub.core.testing.auth_utils import fake_user

from swiss_ai_hub.agent.agents.rag_agent.access.external_access_filters import ExternalAccessFilters
from swiss_ai_hub.agent.agents.rag_agent.configs.external_access_filter_config import ExternalAccessFilterConfig

RESOLVER = "https://lcdm-mcp.example/access/knowledge-codes"
API_KEY = "resolver-key"


@pytest.fixture(autouse=True)
def _fresh_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    ExternalAccessFilters.forget_answers()
    # the test host does not resolve; allowed like a resolver on the company network
    monkeypatch.setenv("EXTERNAL_ACCESS_FILTER_ALLOWED_PRIVATE_HOSTS", "lcdm-mcp.example")


def test_an_internal_resolver_host_is_not_called_unless_allowed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EXTERNAL_ACCESS_FILTER_ALLOWED_PRIVATE_HOSTS", "")
    resolver = _Resolver(httpx.Response(200, json={"values": ["NEST/DOK"]}))
    internal = _config().model_copy(update={"resolver_url": "http://api:8000/values"})

    assert _apply(resolver, internal) == []
    assert resolver.calls == []


def test_an_allowed_internal_resolver_host_is_called(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EXTERNAL_ACCESS_FILTER_ALLOWED_PRIVATE_HOSTS", "acl-stub-resolver")
    resolver = _Resolver(httpx.Response(200, json={"values": ["NEST/DOK"]}))
    internal = _config().model_copy(update={"resolver_url": "http://acl-stub-resolver:8099/values"})

    assert _apply(resolver, internal)[0].additional_metadata_filters[0].value == ["NEST/DOK"]


def _config(cache_ttl_seconds: int = 60) -> ExternalAccessFilterConfig:
    return ExternalAccessFilterConfig(
        metadata_key="lcdm_knowledge_code", resolver_url=RESOLVER, api_key=API_KEY, cache_ttl_seconds=cache_ttl_seconds
    )


def _runtime() -> RetrievalRuntimeConfig:
    return RetrievalRuntimeConfig.from_config(
        KnowledgeRetrieverConfig(
            embed_model=EmbeddingModelConfig(model_name="embedding/test"),
            vector_store=MilvusVectorStoreConfig(
                collection_name="lcdmmuster", dimensions=1024, index_namespaces=["gto"]
            ),
            retrieve_k=5,
        )
    )


class _Resolver:
    def __init__(self, response: httpx.Response | Exception) -> None:
        self.response = response
        self.calls: list[httpx.Request] = []

    def transport(self) -> httpx.MockTransport:
        return httpx.MockTransport(self._handle)

    def _handle(self, request: httpx.Request) -> httpx.Response:
        self.calls.append(request)
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


def _apply(resolver: _Resolver, config: ExternalAccessFilterConfig | None = None, user=None):
    return asyncio.run(
        ExternalAccessFilters.apply([_runtime()], config or _config(), user or fake_user(), resolver.transport())
    )


def test_the_values_the_resolver_releases_become_a_choice_filter() -> None:
    resolver = _Resolver(httpx.Response(200, json={"values": ["NEST/DOK", "KSB/DOK"]}))

    narrowed = _apply(resolver)

    assert narrowed[0].additional_metadata_filters == [
        MetadataFilterPair(key="lcdm_knowledge_code", value=["NEST/DOK", "KSB/DOK"])
    ]
    assert resolver.calls[0].headers["Authorization"] == f"Bearer {API_KEY}"
    assert resolver.calls[0].headers["X-AIHub-User-Email"] == fake_user().email
    assert resolver.calls[0].headers["X-AIHub-Tenant"] == fake_user().acting_within_tenant.id
    assert str(resolver.calls[0].url) == RESOLVER


def test_an_empty_answer_retrieves_nothing() -> None:
    assert _apply(_Resolver(httpx.Response(200, json={"values": []}))) == []


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(403, json={"error": "forbidden"}),
        httpx.Response(500),
        httpx.Response(200, text="not json"),
        httpx.Response(200, json={"codes": ["NEST/DOK"]}),
        httpx.ConnectError("refused"),
        httpx.ReadTimeout("slow"),
    ],
)
def test_a_failing_resolver_retrieves_nothing(response: httpx.Response | Exception) -> None:
    assert _apply(_Resolver(response)) == []


def test_a_user_without_an_e_mail_is_not_asked_about() -> None:
    resolver = _Resolver(httpx.Response(200, json={"values": ["NEST/DOK"]}))

    assert _apply(resolver, user=fake_user().model_copy(update={"email": ""})) == []
    assert resolver.calls == []


def test_without_a_user_nothing_is_retrieved() -> None:
    resolver = _Resolver(httpx.Response(200, json={"values": ["NEST/DOK"]}))

    narrowed = asyncio.run(ExternalAccessFilters.apply([_runtime()], _config(), None, resolver.transport()))

    assert narrowed == []


def test_an_answer_is_reused_within_the_cache_time() -> None:
    resolver = _Resolver(httpx.Response(200, json={"values": ["NEST/DOK"]}))

    _apply(resolver)
    _apply(resolver)

    assert len(resolver.calls) == 1


def test_a_cache_time_of_zero_asks_every_time() -> None:
    resolver = _Resolver(httpx.Response(200, json={"values": ["NEST/DOK"]}))

    _apply(resolver, _config(cache_ttl_seconds=0))
    _apply(resolver, _config(cache_ttl_seconds=0))

    assert len(resolver.calls) == 2


def test_a_failure_is_not_cached() -> None:
    failing = _Resolver(httpx.Response(503))
    _apply(failing)
    answering = _Resolver(httpx.Response(200, json={"values": ["NEST/DOK"]}))

    assert _apply(answering)[0].additional_metadata_filters[0].value == ["NEST/DOK"]


def test_earlier_filters_of_the_run_are_kept() -> None:
    resolver = _Resolver(httpx.Response(200, json={"values": ["NEST/DOK"]}))
    runtime = _runtime().model_copy(
        update={"additional_metadata_filters": [MetadataFilterPair(key="document_type", value="invoice")]}
    )

    narrowed = asyncio.run(ExternalAccessFilters.apply([runtime], _config(), fake_user(), resolver.transport()))

    assert [f.key for f in narrowed[0].additional_metadata_filters] == ["document_type", "lcdm_knowledge_code"]
