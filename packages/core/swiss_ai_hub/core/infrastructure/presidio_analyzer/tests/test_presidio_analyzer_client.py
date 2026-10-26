import json

import httpx
import pytest
from pydantic import SecretStr

from swiss_ai_hub.core.infrastructure.presidio_analyzer.presidio_analyzer_client import PresidioAnalyzerClient
from swiss_ai_hub.core.infrastructure.presidio_analyzer.presidio_analyzer_settings import PresidioAnalyzerSettings

pytestmark = pytest.mark.asyncio

SETTINGS = PresidioAnalyzerSettings(API_BASE="http://analyzer.test/", API_KEY=SecretStr("analyzer-key"))


@pytest.fixture
def requests(monkeypatch: pytest.MonkeyPatch) -> list[httpx.Request]:
    """Every request the client sends, answered with one PERSON span."""
    seen: list[httpx.Request] = []

    def answer(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if request.url.path != "/analyze":
            return httpx.Response(404)
        return httpx.Response(200, json=[{"entity_type": "PERSON", "start": 0, "end": 4, "score": 0.9, "x": 1}])

    real_client = httpx.AsyncClient
    monkeypatch.setattr(
        httpx, "AsyncClient", lambda **kwargs: real_client(transport=httpx.MockTransport(answer), **kwargs)
    )
    return seen


async def test_should_return_the_spans_the_analyzer_found(requests: list[httpx.Request]) -> None:
    spans = await PresidioAnalyzerClient(SETTINGS).analyze("Anna kommt", ["PERSON"])

    assert [(span.entity_type, span.start, span.end) for span in spans] == [("PERSON", 0, 4)]


async def test_should_send_the_text_entities_and_key(requests: list[httpx.Request]) -> None:
    await PresidioAnalyzerClient(SETTINGS).analyze("Anna kommt", ["PERSON", "LOCATION"])

    (request,) = requests
    assert str(request.url) == "http://analyzer.test/analyze"
    assert request.headers["Authorization"] == "Bearer analyzer-key"
    assert json.loads(request.content) == {"text": "Anna kommt", "language": "de", "entities": ["PERSON", "LOCATION"]}


async def test_should_send_the_allow_list_as_a_regex_when_given(requests: list[httpx.Request]) -> None:
    await PresidioAnalyzerClient(SETTINGS).analyze("Anna kommt", ["PERSON"], allow_list_pattern=r"\Asie\Z")

    body = json.loads(requests[0].content)
    assert (body["allow_list"], body["allow_list_match"]) == ([r"\Asie\Z"], "regex")


async def test_should_raise_when_the_analyzer_fails(requests: list[httpx.Request]) -> None:
    settings = SETTINGS.model_copy(update={"API_BASE": "http://analyzer.test/broken"})

    with pytest.raises(httpx.HTTPStatusError):
        await PresidioAnalyzerClient(settings).analyze("Anna kommt", ["PERSON"])
