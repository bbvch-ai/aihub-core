"""How agents' searches reach SearXNG: one JSON request per query, narrowed as the profile asks."""

from pathlib import Path
from typing import Any

import httpx
import pytest
import yaml

from swiss_ai_hub.core.infrastructure.searxng import searxng_client
from swiss_ai_hub.core.infrastructure.searxng.searxng_client import SearxngClient
from swiss_ai_hub.core.infrastructure.searxng.searxng_engine import SearxngEngine
from swiss_ai_hub.core.infrastructure.searxng.searxng_safe_search import SearxngSafeSearch
from swiss_ai_hub.core.infrastructure.searxng.searxng_settings import SearxngSettings

pytestmark = pytest.mark.unit

SEARXNG_SETTINGS = Path(__file__).parents[7] / "infra" / "configs" / "searxng" / "settings.yml"

HITS = [
    {"url": "https://a.example", "title": "A", "content": "first", "engine": "brave"},
    {"url": "", "title": "no link"},
    {"url": "http:///go/v1/AdtkpVUfkX5N", "title": "an engine's unresolved redirect", "engine": "brave"},
    {"url": "javascript:alert(1)", "title": "not a web page", "engine": "brave"},
    {"url": "https://b.example", "title": None, "content": None, "engine": "qwant"},
    {"url": "https://c.example", "title": "C", "content": "third", "engine": "mojeek"},
]


@pytest.fixture
def requests(monkeypatch: pytest.MonkeyPatch) -> list[httpx.Request]:
    recorded: list[httpx.Request] = []

    def respond(request: httpx.Request) -> httpx.Response:
        recorded.append(request)
        if request.url.params["q"] == "broken":
            return httpx.Response(500, text="engine error")
        return httpx.Response(200, json={"query": request.url.params["q"], "results": HITS})

    real_client = httpx.AsyncClient

    def client(**kwargs: Any) -> httpx.AsyncClient:
        return real_client(transport=httpx.MockTransport(respond), **kwargs)

    monkeypatch.setattr(searxng_client.httpx, "AsyncClient", client)
    return recorded


def _client() -> SearxngClient:
    return SearxngClient(SearxngSettings(BASE_URL="http://searxng:8080"))


@pytest.mark.asyncio
async def test_asks_for_json_and_keeps_only_the_hits_linking_to_a_web_page(requests: list[httpx.Request]) -> None:
    results = await _client().search("swiss ai", max_results=10)

    assert [result.url for result in results] == ["https://a.example", "https://b.example", "https://c.example"]
    assert results[1].title == ""
    assert requests[0].url.path == "/search"
    assert requests[0].url.params["format"] == "json"
    assert requests[0].url.params["safesearch"] == "1"
    assert "engines" not in requests[0].url.params
    assert "time_range" not in requests[0].url.params


@pytest.mark.asyncio
async def test_narrows_to_the_engines_period_and_count_asked_for(requests: list[httpx.Request]) -> None:
    results = await _client().search(
        "swiss ai",
        engines=[SearxngEngine.BRAVE, SearxngEngine.WIKIPEDIA],
        language="de",
        safe_search=SearxngSafeSearch.STRICT,
        time_range="week",
        max_results=1,
    )

    assert len(results) == 1
    params = requests[0].url.params
    assert params["engines"] == "brave,wikipedia"
    assert params["language"] == "de"
    assert params["safesearch"] == "2"
    assert params["time_range"] == "week"


@pytest.mark.asyncio
async def test_a_failing_searxng_fails_the_search(requests: list[httpx.Request]) -> None:
    with pytest.raises(httpx.HTTPStatusError):
        await _client().search("broken")


def test_the_engines_a_profile_can_pick_are_the_ones_searxng_runs() -> None:
    """Naming an engine SearXNG does not run returns nothing, so the profile's choices follow the deployed set."""
    settings = yaml.safe_load(SEARXNG_SETTINGS.read_text())

    assert set(SearxngEngine) == set(settings["use_default_settings"]["engines"]["keep_only"])
