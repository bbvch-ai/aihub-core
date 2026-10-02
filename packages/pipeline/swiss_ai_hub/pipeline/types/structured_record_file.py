import re
from typing import Annotated

import yaml
from pydantic import BaseModel, Field, field_validator
from swiss_ai_hub.core.persistence import NamespaceEntity

FrontmatterValue = str | bool | int | float | list[str]

_SEGMENT_MAX_LENGTH = 120
_UNSAFE_SEGMENT_CHARACTERS = re.compile(r"[/\\\x00-\x1f\x7f]")


class StructuredRecordFile(BaseModel):
    """One record of a structured source as the markdown file the ingestion pipeline reads.

    The namespace is sanitised exactly as the ingestion pipeline names namespaces, so the folder and its namespace
    never drift apart. Frontmatter renders with sorted keys, so an unchanged record renders to the same bytes and is
    skipped by hash.
    """

    namespace: Annotated[str, Field(description="Top-level folder; the ingestion pipeline makes it the namespace.")]
    path_segments: Annotated[
        list[str],
        Field(min_length=1, description="Folders below the namespace, then the file name without its extension."),
    ]
    frontmatter: Annotated[
        dict[str, FrontmatterValue | None],
        Field(description="The record's fields; dates as ISO-8601 strings, None values are left out."),
    ] = {}
    body: Annotated[str, Field(description="Markdown text that is chunked and embedded.")]

    @field_validator("namespace")
    @classmethod
    def _namespace_named_like_its_folder(cls, namespace: str) -> str:
        sanitized = NamespaceEntity.sanitize_namespace_name(namespace.strip())
        if not sanitized:
            raise ValueError("A structured record needs a namespace: root-level files are never ingested.")
        return sanitized

    @field_validator("path_segments")
    @classmethod
    def _segments_safe_as_object_key_parts(cls, segments: list[str]) -> list[str]:
        safe = [_UNSAFE_SEGMENT_CHARACTERS.sub("_", segment).strip()[:_SEGMENT_MAX_LENGTH] for segment in segments]
        if any(segment in {"", ".", ".."} for segment in safe):
            raise ValueError(f"Path segments {segments!r} contain an empty or relative segment.")
        return safe

    @property
    def object_key(self) -> str:
        *folders, name = self.path_segments
        return "/".join([self.namespace, *folders, f"{name}.md"])

    @classmethod
    def object_key_for(cls, namespace: str, path_segments: list[str]) -> str:
        """The key a record is written under, for listings that know where a record lives but not its content.

        Built through the same validators as the written file: a listed key that differs from the written one would
        make the removal delete a record the cursor never fetches again.
        """
        return cls(namespace=namespace, path_segments=path_segments, body="").object_key

    def render(self) -> bytes:
        fields = {key: value for key, value in self.frontmatter.items() if value is not None}
        body = self.body if self.body.endswith("\n") else f"{self.body}\n"
        if not fields:
            return body.encode()
        header = yaml.safe_dump(fields, sort_keys=True, allow_unicode=True, default_flow_style=False)
        return f"---\n{header}---\n\n{body}".encode()
