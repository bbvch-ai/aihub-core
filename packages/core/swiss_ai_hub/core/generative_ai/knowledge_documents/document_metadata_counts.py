import json
from typing import Annotated, ClassVar, Self

from pydantic import BaseModel, Field

from swiss_ai_hub.core.generative_ai.knowledge_documents.document_metadata_verdict import DocumentMetadataVerdict


class DocumentMetadataCounts(BaseModel):
    """How a metadata filter sorted the selected documents, so the user sees what it kept, left out and could not tell.

    The examples are bounded in bytes when they are collected, since they ride on every per-document event of a run.
    """

    EXCLUDED_EXAMPLE_LIMIT: ClassVar[int] = 10
    EXCLUDED_EXAMPLE_BYTES: ClassVar[int] = 2_000
    EXCLUDED_PATH_CHARACTERS: ClassVar[int] = 200

    matched: Annotated[int, Field(ge=0, description="Documents whose type and attributes match the filter.")] = 0
    excluded: Annotated[int, Field(ge=0, description="Documents left out, their type or a value fails it.")] = 0
    unknown: Annotated[int, Field(ge=0, description="Documents kept, unclassified or with an empty value.")] = 0
    excluded_examples: Annotated[list[str], Field(description="Some of the left-out paths, in listing order.")] = []

    @property
    def total(self) -> int:
        return self.matched + self.excluded + self.unknown

    @classmethod
    def collect(cls, outcomes: list[tuple[str, DocumentMetadataVerdict]]) -> Self:
        counts = dict.fromkeys(DocumentMetadataVerdict, 0)
        examples: list[str] = []
        example_bytes = 0
        for path, verdict in outcomes:
            counts[verdict] += 1
            if verdict is not DocumentMetadataVerdict.EXCLUDED:
                continue
            example = cls._cut(path)
            size = cls._serialized_bytes(example)
            if len(examples) < cls.EXCLUDED_EXAMPLE_LIMIT and example_bytes + size <= cls.EXCLUDED_EXAMPLE_BYTES:
                examples.append(example)
                example_bytes += size
        return cls(
            matched=counts[DocumentMetadataVerdict.MATCH],
            excluded=counts[DocumentMetadataVerdict.EXCLUDED],
            unknown=counts[DocumentMetadataVerdict.UNKNOWN],
            excluded_examples=examples,
        )

    @classmethod
    def _cut(cls, path: str) -> str:
        if len(path) <= cls.EXCLUDED_PATH_CHARACTERS:
            return path
        return path[: cls.EXCLUDED_PATH_CHARACTERS - 1] + "…"

    @staticmethod
    def _serialized_bytes(path: str) -> int:
        """The bytes the path adds to an event as `ExtractionTable.serialized_bytes` counts a line."""
        return len(json.dumps(path)) - 2 + len("\\n")
