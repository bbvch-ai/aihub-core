import json
import math
import re
import unicodedata
from datetime import UTC, date, datetime
from typing import Annotated, Any, ClassVar, Self
from urllib.parse import urlparse

import yaml
from pydantic import BaseModel, Field
from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import (
    DEFAULT_METADATA,
    DOCUMENT_ID,
    HASH,
    IS_INGESTED,
    NODE_CONTENT,
    NODE_EMBEDDING,
    NODE_ID,
    NODE_METADATA,
    NUMBER_OF_PAGES,
)

from swiss_ai_hub.pipeline.resources.parser.table_refinement_resource import TABLE_REFINEMENT_METADATA_KEY
from swiss_ai_hub.pipeline.types.malformed_frontmatter_error import MalformedFrontmatterError

type MetadataValue = str | int | float | list[str]


class MarkdownFrontmatter(BaseModel):
    """The YAML block a markdown file may open with, split from the body and read into document fields.

    Structured sources write their records as such files (#1890) and people upload them by hand. Chunked as text, the
    block would be embedded as YAML, and its fields could neither be filtered on nor become the document's title and
    link. Keys are normalised because Milvus filter expressions and Mongo field names accept only plain identifiers,
    and an admin has to be able to predict the name to allow it as a filter field.
    """

    RESERVED_FIELDS: ClassVar[frozenset[str]] = frozenset({"title", "url", "created", "updated"})
    PLATFORM_KEYS: ClassVar[frozenset[str]] = frozenset(
        {
            *DEFAULT_METADATA,
            DOCUMENT_ID,
            HASH,
            IS_INGESTED,
            NODE_CONTENT,
            NODE_EMBEDDING,
            NODE_ID,
            NODE_METADATA,
            NUMBER_OF_PAGES,
            TABLE_REFINEMENT_METADATA_KEY,
            "document_parser",
            "doc_id",
            "ref_doc_id",
            "text",
            "sparse_embedding",
        }
    )
    # Every chunk stores its metadata twice in Milvus' 64 KiB dynamic field (as keys and inside _node_content), next
    # to the platform's own keys and the chunk's relationships, so the frontmatter gets a small, fixed share.
    MAX_METADATA_BYTES: ClassVar[int] = 8192
    INT64_RANGE: ClassVar[range] = range(-(2**63), 2**63)
    BLOCK_PATTERN: ClassVar[re.Pattern[str]] = re.compile(
        r"\A﻿?---[ \t]*\r?\n(?P<yaml>.*?)^(?:---|\.\.\.)[ \t]*(?:\r?\n|\Z)", re.DOTALL | re.MULTILINE
    )

    body: Annotated[str, Field(description="The markdown after the block; this is what gets chunked and embedded.")]
    title: Annotated[str | None, Field(description="Becomes the document title.")] = None
    url: Annotated[str | None, Field(description="Becomes the original link citations show; http(s) only.")] = None
    created: Annotated[int | None, Field(description="Becomes the document's creation time, in epoch seconds.")] = None
    updated: Annotated[int | None, Field(description="Becomes the document's update time, in epoch seconds.")] = None
    metadata: Annotated[
        dict[str, MetadataValue],
        Field(description="Every other key under its normalised name, stored on the document and its chunks."),
    ] = {}
    skipped: Annotated[
        dict[str, str], Field(description="Keys left out, as written in the file, with the reason why.")
    ] = {}

    @classmethod
    def from_markdown(cls, text: str) -> Self | None:
        """None when the text does not open with a block, so the file is ingested as before."""
        match = cls.BLOCK_PATTERN.match(text)
        if match is None:
            return None

        frontmatter = cls(body=text[match.end() :])
        for raw_key, value in cls._load_mapping(match.group("yaml")).items():
            frontmatter._add(str(raw_key), value)
        return frontmatter

    @staticmethod
    def normalize_key(key: str) -> str:
        """Lowercase ASCII snake case, accents dropped: `Fix Version` -> `fix_version`, `Priorität` -> `prioritat`.

        Edge underscores are trimmed, so no key can reach the `_`-prefixed names llama-index stores beside it."""
        ascii_key = unicodedata.normalize("NFKD", key).encode("ascii", "ignore").decode()
        return re.sub(r"[^a-z0-9_]+", "_", ascii_key.lower()).strip("_")

    @staticmethod
    def _load_mapping(block: str) -> dict[Any, Any]:
        try:
            loaded = yaml.safe_load(block)
        except yaml.YAMLError as yaml_error:
            raise MalformedFrontmatterError(f"Frontmatter is not valid YAML: {yaml_error}") from yaml_error

        if loaded is None:
            return {}
        if not isinstance(loaded, dict):
            raise MalformedFrontmatterError(f"Frontmatter holds a {type(loaded).__name__}, not key: value pairs")
        return loaded

    def _add(self, raw_key: str, value: object) -> None:
        key = self.normalize_key(raw_key)
        reason = self._reason_to_refuse_name(key)
        if reason is None:
            reason = self._set_reserved(key, value) if key in self.RESERVED_FIELDS else self._set_metadata(key, value)
        if reason is not None:
            self.skipped[raw_key] = reason

    def _reason_to_refuse_name(self, key: str) -> str | None:
        if not re.fullmatch(r"[a-z][a-z0-9_]*", key):
            return "no name starting with a letter is left once it is reduced to a-z, 0-9 and _"
        if key in self.PLATFORM_KEYS:
            return f"'{key}' is a name the platform already uses"
        if key in self.metadata or (key in self.RESERVED_FIELDS and getattr(self, key) is not None):
            return f"an earlier key already became '{key}'"
        return None

    def _set_reserved(self, key: str, value: object) -> str | None:
        match key:
            case "title":
                title = self._as_text(value)
                if not title or not title.strip():
                    return "title must be non-empty text"
                self.title = title.strip()
            case "url":
                if not self._is_web_link(value):
                    return "url must be an http or https link"
                self.url = str(value).strip()
            case _:
                timestamp = self._as_timestamp(value)
                if timestamp is None:
                    return f"{key} must be an ISO 8601 date, such as 2026-09-30 or 2026-09-30T14:05:00+02:00"
                setattr(self, key, timestamp)
        return None

    def _set_metadata(self, key: str, value: object) -> str | None:
        stored = self._as_metadata_value(value)
        if stored is None:
            return "values must be text, a number, true/false, a date, or a list of those"
        if self._json_size_in_bytes({**self.metadata, key: stored}) > self.MAX_METADATA_BYTES:
            return f"the frontmatter metadata would exceed {self.MAX_METADATA_BYTES} bytes"
        self.metadata[key] = stored
        return None

    @classmethod
    def _as_metadata_value(cls, value: object) -> MetadataValue | None:
        """true/false and dates become text: a retrieval filter cannot carry a boolean, and no store keeps a date type a
        filter could match. List items all become text, which is what a filter value is compared with."""
        match value:
            case str() | bool() | date():
                return cls._as_text(value)
            case int() if value in cls.INT64_RANGE:
                return value
            case float() if math.isfinite(value):
                return value
            case list():
                items = [cls._as_text(item) for item in value]
                return None if None in items else items
            case _:
                return None

    @staticmethod
    def _as_text(value: object) -> str | None:
        match value:
            case str():
                return value
            case bool():
                return "true" if value else "false"
            case int() | float():
                return str(value)
            case date():
                return value.isoformat()
            case _:
                return None

    @staticmethod
    def _is_web_link(value: object) -> bool:
        """Citations render the link as a clickable href, so a `javascript:` or any other scheme is refused."""
        if not isinstance(value, str):
            return False
        parsed = urlparse(value.strip())
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)

    @staticmethod
    def _as_timestamp(value: object) -> int | None:
        """Numbers are refused: epoch seconds and milliseconds cannot be told apart, and a file's writer can always say
        ISO 8601. A time without a zone is read as UTC."""
        match value:
            case datetime():
                moment = value
            case date():
                moment = datetime(value.year, value.month, value.day)
            case str():
                try:
                    moment = datetime.fromisoformat(value.strip())
                except ValueError:
                    return None
            case _:
                return None
        return int((moment if moment.tzinfo else moment.replace(tzinfo=UTC)).timestamp())

    @staticmethod
    def _json_size_in_bytes(value: object) -> int:
        """Measured the way pymilvus packs the dynamic field: compact separators, raw UTF-8."""
        return len(json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode())
