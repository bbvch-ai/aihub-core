import asyncio
import hashlib
import importlib.metadata
import json
import logging
import os
from typing import ClassVar

from swiss_ai_hub.core.generative_ai.document.loaders.parse_cache_bucket import ParseCacheBucket
from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.smart_tracer import get_tracer

logger = logging.getLogger(__name__)

PARSE_CACHE_HIT_ATTRIBUTE = "aihub.markitdown.parse_cache.hit"
PARSE_CACHE_KEY_ATTRIBUTE = "aihub.markitdown.parse_cache.key"


class MarkItDownParseCache:
    """
    Office conversions keyed by the document's bytes, so OpenWebUI's upload parse, an agent reading the same attachment
    on every turn, and ingestion convert a document once.

    A large spreadsheet is the reason: each read of a 100,000-row sheet was a full conversion. Entries are not
    tenant-scoped, as with `MineruParseCache`: the key can only be derived from the exact bytes. What changes the output
    is part of the key, so a new MarkItDown release or a change to our own xlsx rendering starts fresh.
    """

    XLSX_FORMAT: ClassVar[int] = 1

    def __init__(self) -> None:
        self._bucket = ParseCacheBucket()

    async def get(self, file_bytes: bytes, filename: str) -> str | None:
        """Traced by hand rather than with `trace_fn`, which would record the document's bytes and its text."""
        key = self.object_key(file_bytes, filename)
        with get_tracer(__name__).start_as_current_span(
            "MarkItDownParseCache.get", attributes={PARSE_CACHE_KEY_ATTRIBUTE: key}
        ) as span:
            content = await asyncio.to_thread(self._bucket.read, key)
            span.set_attribute(PARSE_CACHE_HIT_ATTRIBUTE, content is not None)
        return None if content is None else content.decode()

    async def put(self, file_bytes: bytes, filename: str, markdown: str) -> None:
        key = self.object_key(file_bytes, filename)
        with get_tracer(__name__).start_as_current_span(
            "MarkItDownParseCache.put", attributes={PARSE_CACHE_KEY_ATTRIBUTE: key}
        ):
            await asyncio.to_thread(self._bucket.write, key, markdown.encode(), "text/markdown; charset=utf-8")
        logger.debug(f"[MarkItDownParseCache] Stored {filename} as {key}")

    def object_key(self, file_bytes: bytes, filename: str) -> str:
        """The extension is part of the key because it picks the converter: the same bytes as .xlsx and .docx differ."""
        extension = os.path.splitext(filename)[1].lower()
        content_hash = hashlib.sha256(file_bytes).hexdigest()
        return f"markitdown/{self.settings_fingerprint()}/{content_hash}{extension}/markdown.md"

    @classmethod
    def settings_fingerprint(cls) -> str:
        relevant = {"markitdown": importlib.metadata.version("markitdown"), "xlsx_format": cls.XLSX_FORMAT}
        return hashlib.sha256(json.dumps(relevant, sort_keys=True).encode()).hexdigest()[:16]
