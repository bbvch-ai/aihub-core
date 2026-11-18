import json
from pathlib import Path
from typing import ClassVar

import yaml

from swiss_ai_hub.core.generative_ai.document.classification.tests.evaluation.classification_case import (
    ClassificationCase,
)
from swiss_ai_hub.core.generative_ai.document.extraction.document_extractor import DocumentExtractor


class ClassificationCorpus:
    """Loads the samples the evaluation runs on.

    The synthetic sample is committed: documents written for the evaluation with made-up companies, each YAML file a
    list of cases. Real documents are confidential and stay outside the repository; a label file names them. It is
    JSON Lines, one case per line:

        {"file": "zugferd/acme-0042.pdf", "kind": "invoice", "expected": {"document_date": "2025-03-14", ...}}

    `file` is relative to the label file. Markdown and text files are read as they are; any other file is parsed the
    way ingestion parses it (MinerU for PDFs, through `DocumentExtractor`), so the classifier sees the same text.
    """

    SYNTHETIC_DIRECTORY: ClassVar[Path] = Path(__file__).parent / "synthetic"
    TEXT_SUFFIXES: ClassVar[frozenset[str]] = frozenset({".md", ".txt"})

    @classmethod
    def synthetic(cls) -> list[ClassificationCase]:
        cases = [
            ClassificationCase(**item)
            for path in sorted(cls.SYNTHETIC_DIRECTORY.glob("*.yaml"))
            for item in yaml.safe_load(path.read_text(encoding="utf-8"))
        ]
        cls._ensure_unique(cases)
        return cases

    @classmethod
    async def from_label_file(cls, label_file: Path) -> list[ClassificationCase]:
        cases = []
        for line in label_file.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            label = json.loads(line)
            path = label_file.parent / label["file"]
            cases.append(
                ClassificationCase(
                    id=label["file"],
                    kind=label["kind"],
                    title=path.name,
                    text=await cls._text(path),
                    expected=label.get("expected", {}),
                    note=label.get("note"),
                )
            )
        cls._ensure_unique(cases)
        return cases

    @classmethod
    async def _text(cls, path: Path) -> str:
        if path.suffix.lower() in cls.TEXT_SUFFIXES:
            return path.read_text(encoding="utf-8")
        extracted = await DocumentExtractor.extract_from_bytes(path.read_bytes(), path.name)
        return extracted.content

    @staticmethod
    def _ensure_unique(cases: list[ClassificationCase]) -> None:
        ids = [case.id for case in cases]
        duplicates = sorted({case_id for case_id in ids if ids.count(case_id) > 1})
        if duplicates:
            raise ValueError(f"duplicate case ids: {duplicates}")
