import asyncio
import hashlib
import json
import logging
import os
from typing import ClassVar

from swiss_ai_hub.core.generative_ai.document.loaders.mineru_file_result import MineruFileResult
from swiss_ai_hub.core.generative_ai.document.loaders.parse_cache_bucket import ParseCacheBucket
from swiss_ai_hub.core.infrastructure.mineru.mineru_settings import MineruSettings
from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.smart_tracer import get_tracer

logger = logging.getLogger(__name__)

PARSE_CACHE_HIT_ATTRIBUTE = "aihub.mineru.parse_cache.hit"
PARSE_CACHE_KEY_ATTRIBUTE = "aihub.mineru.parse_cache.key"


class MineruParseCache:
    """
    MinerU conversions keyed by the document's bytes, so OpenWebUI's upload parse and an agent's parse of the
    same attachment cost one OCR run.

    Entries are not tenant-scoped: the key can only be derived from the exact bytes, and identical bytes give
    identical output. The settings that change MinerU's output are part of the key, so changing them starts
    fresh. Entries expire through the bucket's lifecycle rule (`s3-init-buckets.sh.j2`).
    """

    WITH_IMAGES: ClassVar[str] = "with-images"
    TEXT_ONLY: ClassVar[str] = "text-only"

    def __init__(self, settings: MineruSettings) -> None:
        self._settings = settings
        self._bucket = ParseCacheBucket()

    async def get(self, file_bytes: bytes, filename: str, include_images: bool) -> MineruFileResult | None:
        """A conversion with images also serves a caller that asked for none.

        Traced by hand rather than with `trace_fn`, which would record the document's bytes and its converted text.
        """
        variants = [self.WITH_IMAGES] if include_images else [self.TEXT_ONLY, self.WITH_IMAGES]
        with get_tracer(__name__).start_as_current_span("MineruParseCache.get") as span:
            for variant in variants:
                key = self.object_key(file_bytes, filename, variant)
                content = await asyncio.to_thread(self._read_object, key)
                if content is not None:
                    span.set_attributes({PARSE_CACHE_HIT_ATTRIBUTE: True, PARSE_CACHE_KEY_ATTRIBUTE: key})
                    return MineruFileResult.model_validate_json(content)
            span.set_attribute(PARSE_CACHE_HIT_ATTRIBUTE, False)
            return None

    async def put(self, file_bytes: bytes, filename: str, include_images: bool, result: MineruFileResult) -> None:
        variant = self.WITH_IMAGES if include_images else self.TEXT_ONLY
        key = self.object_key(file_bytes, filename, variant)
        with get_tracer(__name__).start_as_current_span(
            "MineruParseCache.put", attributes={PARSE_CACHE_KEY_ATTRIBUTE: key}
        ):
            await asyncio.to_thread(self._write_object, key, result.model_dump_json().encode())
        logger.debug(f"[MineruParseCache] Stored {filename} as {key}")

    def object_key(self, file_bytes: bytes, filename: str, variant: str) -> str:
        """The extension is part of the key because MinerU routes a PDF and an image of the same bytes differently."""
        extension = os.path.splitext(filename)[1].lower()
        content_hash = hashlib.sha256(file_bytes).hexdigest()
        return f"mineru/{self.settings_fingerprint()}/{content_hash}{extension}/{variant}.json"

    def settings_fingerprint(self) -> str:
        """Only what changes the output: the service URLs do not, the page batching does, and so does the output
        format, whose version retires entries written before a change to it (2: page breaks)."""
        relevant = {
            "vlm_name": self._settings.VLM_NAME,
            "formula_enable": self._settings.FORMULA_ENABLE,
            "table_enable": self._settings.TABLE_ENABLE,
            "page_batch_size": self._settings.PAGE_BATCH_SIZE,
            "output_format": 2,
        }
        return hashlib.sha256(json.dumps(relevant, sort_keys=True).encode()).hexdigest()[:16]

    def _read_object(self, key: str) -> bytes | None:
        return self._bucket.read(key)

    def _write_object(self, key: str, content: bytes) -> None:
        self._bucket.write(key, content, "application/json")
