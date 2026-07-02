"""LiteLLM pre-call hook that inlines RAG figures as base64 at the provider boundary.

RAG figures reach LiteLLM as an image **URL** signed against our internal object
storage. The LLM provider dereferences image URLs server-side and cannot reach that
storage (managed inference fetches through its own egress proxy → 403). LiteLLM is
in-cluster and *can* reach the storage, so this hook fetches each such figure just
before the provider call and replaces the URL with a `data:` base64 URL. The heavy
base64 exists only transiently here and never touches NATS/Mongo/Langfuse.

The module is bind-mounted into the upstream LiteLLM image (no Dockerfile), so it may
only depend on the stdlib, httpx, and LiteLLM's own `CustomLogger`. It CANNOT import
`swiss_ai_hub.*` — that package is not installed in the LiteLLM image. All behaviour
is env-driven and read at import time.
"""

import base64
import logging
import mimetypes
import os
from urllib.parse import urlparse

import httpx

try:
    from litellm.integrations.custom_logger import CustomLogger
except ImportError:
    # litellm is absent outside its own image (e.g. unit tests import this by path).
    CustomLogger = object

logger = logging.getLogger(__name__)


def _env_bool(name: str, default: bool) -> bool:
    return os.environ.get(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


INLINE_ENABLED = _env_bool("RAG_IMAGE_INLINE_ENABLED", True)
INLINE_MAX_BYTES = int(os.environ.get("RAG_IMAGE_INLINE_MAX_BYTES", 5 * 1024 * 1024))
S3_STORAGE_HOST = urlparse(os.environ.get("S3_STORAGE_ENDPOINT", "")).netloc

FETCH_FAILED_MARKER = "[failed to fetch figure/image]"
TOO_LARGE_MARKER = "[figure omitted: exceeds size limit]"


class RagImageInliner(CustomLogger):
    """Downloads internal-S3 figure URLs and inlines them as base64 `data:` URLs.

    A figure that cannot be fetched or exceeds the size cap degrades to a short text
    marker in place of the image, so one bad figure never fails the whole LLM call.
    """

    async def async_pre_call_hook(self, user_api_key_dict, cache, data, call_type):
        if not INLINE_ENABLED or not S3_STORAGE_HOST:
            return data

        for message in data.get("messages", []):
            content = message.get("content")
            if not isinstance(content, list):
                continue
            for part in content:
                if not isinstance(part, dict) or part.get("type") != "image_url":
                    continue
                url = part.get("image_url", {}).get("url", "")
                if urlparse(url).netloc != S3_STORAGE_HOST:
                    continue
                await self._inline_or_degrade(part, url)

        return data

    async def _inline_or_degrade(self, part: dict, url: str) -> None:
        try:
            image_bytes, content_type = await self._download(url)
        except Exception as exc:
            logger.warning("Failed to fetch RAG figure %s: %s", url, exc)
            self._replace_with_text(part, FETCH_FAILED_MARKER)
            return

        if len(image_bytes) > INLINE_MAX_BYTES:
            logger.warning(
                "RAG figure exceeds inline size limit (%d > %d bytes): %s", len(image_bytes), INLINE_MAX_BYTES, url
            )
            self._replace_with_text(part, TOO_LARGE_MARKER)
            return

        encoded = base64.b64encode(image_bytes).decode()
        part["image_url"]["url"] = f"data:{content_type};base64,{encoded}"

    @staticmethod
    async def _download(url: str) -> tuple[bytes, str]:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            image_bytes = response.content
        content_type = response.headers.get("content-type") or mimetypes.guess_type(url)[0] or "image/jpeg"
        return image_bytes, content_type

    @staticmethod
    def _replace_with_text(part: dict, text: str) -> None:
        part.clear()
        part["type"] = "text"
        part["text"] = text


proxy_handler_instance = RagImageInliner()
