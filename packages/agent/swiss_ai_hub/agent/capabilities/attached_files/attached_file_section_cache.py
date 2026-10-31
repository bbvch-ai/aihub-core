import asyncio
import base64
import hashlib
import inspect
import json
import logging
from array import array
from collections.abc import Callable
from functools import partial
from typing import ClassVar

from botocore.exceptions import BotoCoreError, ClientError
from pydantic import TypeAdapter
from swiss_ai_hub.core.generative_ai import (
    MAX_NODE_TOKENS,
    IngestedNode,
    MarkdownStructuralNodeParser,
    ParseCacheBucket,
)
from swiss_ai_hub.core.infrastructure import get_tracer

from swiss_ai_hub.agent.capabilities.attached_files.attached_file_record import AttachedFileRecord

logger = logging.getLogger(__name__)

CACHE_HIT_ATTRIBUTE = "aihub.attached_files.section_cache.hit"
CACHE_KEY_ATTRIBUTE = "aihub.attached_files.section_cache.key"
SECTIONS = TypeAdapter(list[IngestedNode])
JSON = "application/json"


class AttachedFileSectionCache:
    """
    An attached file's sections and their embeddings, kept so a file asked about on every turn is split and embedded
    once rather than on every read.

    Three kinds of entry live in the parse-cache bucket and expire with it. A record per upload, keyed by the upload's
    agent-scoped location so a file id never answers under another profile, points to the content. The sections and
    embeddings are keyed by a hash of the extracted text, so a re-upload or another chat reuses them; like the parse
    caches, those are not tenant-scoped, because the key can only be derived from the content itself. The cache is
    best-effort: storage it cannot reach costs the time it saves, never the read. Two rankings of the same content at
    once each write the embeddings they know of, and the last write wins; the vectors it drops are embedded again when
    a later question needs them.
    """

    FORMAT: ClassVar[int] = 2
    PREFIX: ClassVar[str] = "attached-files"

    def __init__(self) -> None:
        self._bucket = ParseCacheBucket()

    async def record(self, bucket: str, key: str) -> AttachedFileRecord | None:
        content = await self._read(self.record_key(bucket, key))
        return self._parse(content, AttachedFileRecord.model_validate_json)

    async def put_record(self, bucket: str, key: str, record: AttachedFileRecord) -> None:
        await self._write(self.record_key(bucket, key), record.model_dump_json().encode(), JSON)

    async def sections(self, content_sha256: str, tokenizer_id: str) -> list[IngestedNode] | None:
        content = await self._read(self.sections_key(content_sha256, tokenizer_id))
        return await asyncio.to_thread(self._parse, content, SECTIONS.validate_json)

    async def put_sections(self, content_sha256: str, tokenizer_id: str, sections: list[IngestedNode]) -> None:
        encoded = await asyncio.to_thread(SECTIONS.dump_json, sections)
        await self._write(self.sections_key(content_sha256, tokenizer_id), encoded, JSON)

    async def embeddings(self, content_sha256: str, model: str, sections_digest: str) -> dict[int, array]:
        content = await self._read(self.embeddings_key(content_sha256, model))
        decode = partial(self.decode_embeddings, sections_digest=sections_digest)
        return await asyncio.to_thread(self._parse, content, decode) or {}

    async def put_embeddings(
        self, content_sha256: str, model: str, vectors: dict[int, array], sections_digest: str
    ) -> None:
        encoded = await asyncio.to_thread(self.encode_embeddings, vectors, sections_digest)
        await self._write(self.embeddings_key(content_sha256, model), encoded, JSON)

    @classmethod
    def record_key(cls, bucket: str, key: str) -> str:
        return f"{cls.PREFIX}/by-upload/{hashlib.sha256(f'{bucket}/{key}'.encode()).hexdigest()}.json"

    @classmethod
    def sections_key(cls, content_sha256: str, tokenizer_id: str) -> str:
        """Sections are sized in the embedding model's tokens, so agents ranking with models that count differently
        keep apart sections cut differently from the same content."""
        return f"{cls.PREFIX}/{cls.settings_fingerprint()}/{content_sha256}/sections/{tokenizer_id}.json"

    @classmethod
    def embeddings_key(cls, content_sha256: str, model: str) -> str:
        slug = hashlib.sha256(model.encode()).hexdigest()[:16]
        return f"{cls.PREFIX}/{cls.settings_fingerprint()}/{content_sha256}/embeddings/{slug}.json"

    @classmethod
    def settings_fingerprint(cls) -> str:
        """What changes the sections is part of the key, so a new chunking starts fresh instead of mixing old ones."""
        defaults = inspect.signature(MarkdownStructuralNodeParser.from_defaults).parameters
        relevant = {
            "chunk_size": defaults["chunk_size"].default,
            "chunk_overlap": defaults["chunk_overlap"].default,
            "max_node_tokens": MAX_NODE_TOKENS,
            "format": cls.FORMAT,
        }
        return hashlib.sha256(json.dumps(relevant, sort_keys=True).encode()).hexdigest()[:16]

    @staticmethod
    def sections_digest(sections: list[IngestedNode]) -> str:
        """Embeddings are stored by section index, so they may only meet the sections they were computed for: a
        parser that splits the same text differently would otherwise pair them with other text."""
        digest = hashlib.sha256()
        for section in sections:
            digest.update(f"{section.index}:{len(section.content)}:".encode())
            digest.update(section.content.encode())
        return digest.hexdigest()

    @staticmethod
    def encode_embeddings(vectors: dict[int, array], sections_digest: str) -> bytes:
        indices = sorted(vectors)
        packed = array("f")
        for index in indices:
            packed.extend(vectors[index])
        width = len(vectors[indices[0]]) if indices else 0
        return json.dumps(
            {
                "sections": sections_digest,
                "width": width,
                "indices": indices,
                "vectors": base64.b64encode(packed.tobytes()).decode(),
            }
        ).encode()

    @staticmethod
    def decode_embeddings(content: bytes, sections_digest: str) -> dict[int, array]:
        """Vectors computed for other sections are of no use, and a payload whose size does not add up is refused
        rather than sliced into vectors of the wrong width."""
        payload = json.loads(content)
        if payload["sections"] != sections_digest:
            return {}
        indices: list[int] = payload["indices"]
        width: int = payload["width"]
        packed = array("f")
        packed.frombytes(base64.b64decode(payload["vectors"]))
        if len(packed) != width * len(indices):
            raise ValueError(f"{len(packed)} floats do not make {len(indices)} vectors of width {width}")
        return {index: packed[position * width : (position + 1) * width] for position, index in enumerate(indices)}

    @staticmethod
    def _parse[T](content: bytes | None, decode: Callable[[bytes], T]) -> T | None:
        """An entry that no longer decodes, written by an older format, counts as a miss."""
        if content is None:
            return None
        try:
            return decode(content)
        except (ValueError, KeyError, TypeError):
            logger.warning("[AttachedFileSectionCache] Ignoring an entry that does not decode", exc_info=True)
            return None

    async def _read(self, key: str) -> bytes | None:
        with get_tracer(__name__).start_as_current_span(
            "AttachedFileSectionCache.get", attributes={CACHE_KEY_ATTRIBUTE: key}
        ) as span:
            try:
                content = await asyncio.to_thread(self._bucket.read, key)
            except (BotoCoreError, ClientError):
                logger.warning(f"[AttachedFileSectionCache] Could not read {key}", exc_info=True)
                content = None
            span.set_attribute(CACHE_HIT_ATTRIBUTE, content is not None)
        return content

    async def _write(self, key: str, content: bytes, content_type: str) -> None:
        with get_tracer(__name__).start_as_current_span(
            "AttachedFileSectionCache.put", attributes={CACHE_KEY_ATTRIBUTE: key}
        ):
            try:
                await asyncio.to_thread(self._bucket.write, key, content, content_type)
            except (BotoCoreError, ClientError):
                logger.warning(f"[AttachedFileSectionCache] Could not store {key}", exc_info=True)
