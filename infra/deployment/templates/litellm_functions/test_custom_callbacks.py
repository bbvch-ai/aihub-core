"""Self-contained unit tests for the LiteLLM RAG-figure inlining hook.

This module lives under `infra/deployment/templates/` and is NOT part of a CI
`make test` scope. Run it explicitly:

    uv run pytest infra/deployment/templates/litellm_functions/

The tests import `custom_callbacks` by path with env vars set, and monkeypatch
`httpx.AsyncClient` with a streaming fake so no network access is needed.
"""

import asyncio
import base64
import importlib.util
import sys
from pathlib import Path

import httpx

MODULE_PATH = Path(__file__).parent / "custom_callbacks.py"


def _load_module(monkeypatch, **env):
    for key, value in {
        "S3_STORAGE_ENDPOINT": "http://seaweedfs-s3:9000",
        "RAG_IMAGE_INLINE_ENABLED": "true",
        "RAG_IMAGE_INLINE_MAX_BYTES": "5242880",
        **env,
    }.items():
        monkeypatch.setenv(key, value)
    sys.modules.pop("custom_callbacks", None)
    spec = importlib.util.spec_from_file_location("custom_callbacks", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _FakeStreamResponse:
    def __init__(self, chunks: list[bytes], content_type: str = "image/png"):
        self._chunks = chunks
        self.headers = {"content-type": content_type}

    def raise_for_status(self):
        return None

    async def aiter_bytes(self):
        for chunk in self._chunks:
            yield chunk


def _fake_client(chunks: list[bytes] | None = None, content_type: str = "image/png", stream_error=None):
    """Build a fake httpx.AsyncClient whose `stream()` yields the given chunks (or raises)."""

    class _StreamCtx:
        async def __aenter__(self):
            if stream_error is not None:
                raise stream_error
            return _FakeStreamResponse(chunks or [], content_type)

        async def __aexit__(self, *args):
            return False

    class _FakeAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        def stream(self, method, url):
            return _StreamCtx()

    return _FakeAsyncClient


def _image_message(url: str) -> dict:
    return {"messages": [{"role": "user", "content": [{"type": "image_url", "image_url": {"url": url}}]}]}


_S3_URL = "http://seaweedfs-s3:9000/bucket/fig.png"


def test_internal_s3_image_url_is_inlined_as_base64(monkeypatch):
    module = _load_module(monkeypatch)
    image_bytes = b"\x89PNGfake"
    monkeypatch.setattr(module.httpx, "AsyncClient", _fake_client(chunks=[image_bytes[:4], image_bytes[4:]]))

    data = {
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "describe"},
                    {"type": "image_url", "image_url": {"url": _S3_URL}},
                ],
            }
        ]
    }

    result = asyncio.run(module.proxy_handler_instance.async_pre_call_hook(None, None, data, "completion"))

    expected = f"data:image/png;base64,{base64.b64encode(image_bytes).decode()}"
    assert result["messages"][0]["content"][1]["image_url"]["url"] == expected


def test_non_matching_url_is_left_untouched(monkeypatch):
    module = _load_module(monkeypatch)
    monkeypatch.setattr(module.httpx, "AsyncClient", _fake_client(stream_error=AssertionError("should not fetch")))

    original = "https://example.com/other.png"
    data = _image_message(original)

    result = asyncio.run(module.proxy_handler_instance.async_pre_call_hook(None, None, data, "completion"))

    assert result["messages"][0]["content"][0]["image_url"]["url"] == original


def test_download_error_degrades_to_text_marker(monkeypatch):
    module = _load_module(monkeypatch)
    monkeypatch.setattr(module.httpx, "AsyncClient", _fake_client(stream_error=httpx.ConnectError("boom")))

    result = asyncio.run(module.proxy_handler_instance.async_pre_call_hook(None, None, _image_message(_S3_URL), "completion"))

    assert result["messages"][0]["content"][0] == {"type": "text", "text": module.FETCH_FAILED_MARKER}


def test_oversized_figure_degrades_to_text_marker(monkeypatch):
    module = _load_module(monkeypatch, RAG_IMAGE_INLINE_MAX_BYTES="4")
    monkeypatch.setattr(module.httpx, "AsyncClient", _fake_client(chunks=[b"12", b"345"]))

    result = asyncio.run(module.proxy_handler_instance.async_pre_call_hook(None, None, _image_message(_S3_URL), "completion"))

    assert result["messages"][0]["content"][0] == {"type": "text", "text": module.TOO_LARGE_MARKER}


def test_non_image_content_type_degrades_to_text_marker(monkeypatch):
    module = _load_module(monkeypatch)
    monkeypatch.setattr(module.httpx, "AsyncClient", _fake_client(chunks=[b"<xml>error</xml>"], content_type="text/html"))

    result = asyncio.run(module.proxy_handler_instance.async_pre_call_hook(None, None, _image_message(_S3_URL), "completion"))

    assert result["messages"][0]["content"][0] == {"type": "text", "text": module.FETCH_FAILED_MARKER}


def test_disabled_returns_payload_unchanged(monkeypatch):
    module = _load_module(monkeypatch, RAG_IMAGE_INLINE_ENABLED="false")
    monkeypatch.setattr(module.httpx, "AsyncClient", _fake_client(stream_error=AssertionError("should not fetch")))

    data = _image_message(_S3_URL)
    result = asyncio.run(module.proxy_handler_instance.async_pre_call_hook(None, None, data, "completion"))

    assert result["messages"][0]["content"][0]["image_url"]["url"] == _S3_URL
