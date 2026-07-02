"""Self-contained unit tests for the LiteLLM RAG-figure inlining hook.

This module lives under `infra/deployment/templates/` and is NOT part of a CI
`make test` scope. Run it explicitly:

    uv run pytest infra/deployment/templates/litellm_functions/

The tests import `custom_callbacks` by path with env vars set, and monkeypatch
`httpx.AsyncClient` so no network access is needed.
"""

import asyncio
import base64
import importlib.util
import sys
from pathlib import Path

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


class _FakeResponse:
    def __init__(self, content: bytes, content_type: str = "image/png", status_code: int = 200):
        self.content = content
        self.headers = {"content-type": content_type}
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


def _fake_client(response=None, get_error=None):
    class _FakeAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def get(self, url):
            if get_error is not None:
                raise get_error
            return response

    return _FakeAsyncClient


def test_internal_s3_image_url_is_inlined_as_base64(monkeypatch):
    module = _load_module(monkeypatch)
    image_bytes = b"\x89PNGfake"
    monkeypatch.setattr(module.httpx, "AsyncClient", _fake_client(_FakeResponse(image_bytes)))

    data = {
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "describe"},
                    {"type": "image_url", "image_url": {"url": "http://seaweedfs-s3:9000/bucket/fig.png?sig=x"}},
                ],
            }
        ]
    }

    result = asyncio.run(module.proxy_handler_instance.async_pre_call_hook(None, None, data, "completion"))

    expected = f"data:image/png;base64,{base64.b64encode(image_bytes).decode()}"
    assert result["messages"][0]["content"][1]["image_url"]["url"] == expected


def test_non_matching_url_is_left_untouched(monkeypatch):
    module = _load_module(monkeypatch)
    monkeypatch.setattr(module.httpx, "AsyncClient", _fake_client(get_error=AssertionError("should not fetch")))

    original = "https://example.com/other.png"
    data = {"messages": [{"role": "user", "content": [{"type": "image_url", "image_url": {"url": original}}]}]}

    result = asyncio.run(module.proxy_handler_instance.async_pre_call_hook(None, None, data, "completion"))

    assert result["messages"][0]["content"][0]["image_url"]["url"] == original


def test_download_error_degrades_to_text_marker(monkeypatch):
    module = _load_module(monkeypatch)
    monkeypatch.setattr(module.httpx, "AsyncClient", _fake_client(get_error=RuntimeError("boom")))

    data = {
        "messages": [
            {"role": "user", "content": [{"type": "image_url", "image_url": {"url": "http://seaweedfs-s3:9000/b/f.png"}}]}
        ]
    }

    result = asyncio.run(module.proxy_handler_instance.async_pre_call_hook(None, None, data, "completion"))

    assert result["messages"][0]["content"][0] == {"type": "text", "text": "[failed to fetch figure/image]"}


def test_oversized_figure_degrades_to_text_marker(monkeypatch):
    module = _load_module(monkeypatch, RAG_IMAGE_INLINE_MAX_BYTES="4")
    monkeypatch.setattr(module.httpx, "AsyncClient", _fake_client(_FakeResponse(b"12345")))

    data = {
        "messages": [
            {"role": "user", "content": [{"type": "image_url", "image_url": {"url": "http://seaweedfs-s3:9000/b/f.png"}}]}
        ]
    }

    result = asyncio.run(module.proxy_handler_instance.async_pre_call_hook(None, None, data, "completion"))

    assert result["messages"][0]["content"][0] == {"type": "text", "text": "[figure omitted: exceeds size limit]"}


def test_disabled_returns_payload_unchanged(monkeypatch):
    module = _load_module(monkeypatch, RAG_IMAGE_INLINE_ENABLED="false")
    monkeypatch.setattr(module.httpx, "AsyncClient", _fake_client(get_error=AssertionError("should not fetch")))

    url = "http://seaweedfs-s3:9000/bucket/fig.png"
    data = {"messages": [{"role": "user", "content": [{"type": "image_url", "image_url": {"url": url}}]}]}

    result = asyncio.run(module.proxy_handler_instance.async_pre_call_hook(None, None, data, "completion"))

    assert result["messages"][0]["content"][0]["image_url"]["url"] == url
