from collections.abc import Callable
from typing import Any
from unittest.mock import MagicMock

import httpx
import pytest
import requests
from aiohttp import TraceRequestStartParams
from multidict import CIMultiDict
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from yarl import URL

from swiss_ai_hub.core.infrastructure.opentelemetry.aihub_instrumentor import (
    CustomSpanAttributes,
    aiohttp_request_hook,
    httpx_async_request_hook,
    requests_hook,
)

pytestmark = pytest.mark.unit

_URL_WITH_SECRET = "http://litellm:4000/key/info?key=sk-secret"
_URL_WITHOUT_QUERY = "http://litellm:4000/key/info"


@pytest.mark.asyncio
async def test_httpx_spans_carry_no_query_string() -> None:
    """
    Runs the real instrumentor, because the hook has to replace the URL it records: OpenTelemetry redacts only a few
    signature parameters from it.
    """
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    client = httpx.AsyncClient(transport=httpx.MockTransport(lambda _: httpx.Response(200)))
    HTTPXClientInstrumentor.instrument_client(client, tracer_provider=provider, request_hook=httpx_async_request_hook)

    await client.get(_URL_WITH_SECRET)
    HTTPXClientInstrumentor.uninstrument_client(client)
    await client.aclose()

    span = exporter.get_finished_spans()[0]
    assert span.name == f"GET {_URL_WITHOUT_QUERY}"
    assert span.attributes[CustomSpanAttributes.HTTP_URL] == _URL_WITHOUT_QUERY
    assert [value for value in span.attributes.values() if "sk-secret" in str(value)] == []


@pytest.mark.parametrize(
    ("hook", "request_info"),
    [
        (requests_hook, requests.Request("GET", _URL_WITH_SECRET).prepare()),
        (aiohttp_request_hook, TraceRequestStartParams(method="GET", url=URL(_URL_WITH_SECRET), headers=CIMultiDict())),
    ],
    ids=["requests", "aiohttp"],
)
def test_requests_and_aiohttp_spans_carry_no_query_string(hook: Callable[[Any, Any], None], request_info: Any) -> None:
    span = MagicMock()

    hook(span, request_info)

    span.update_name.assert_called_once_with(f"GET {_URL_WITHOUT_QUERY}")
    assert span.set_attributes.call_args.kwargs["attributes"][CustomSpanAttributes.HTTP_URL] == _URL_WITHOUT_QUERY
