import re
from collections import Counter
from typing import Annotated

from swiss_ai_hub.core.generative_ai import KnowledgeDocumentSummary
from swiss_ai_hub.core.i18n import LocaleHandler

MAX_ENTRIES = 8
_YEAR = re.compile(r"(?<!\d)(?:19|20)\d{2}(?!\d)")


class SelectionFacets:
    """How a broad selection breaks down, so the user can narrow it: by folder, by a year in the path and by
    collection, counted from the listing alone, and a small sample spread over the largest folders."""

    @staticmethod
    def lines(
        documents: Annotated[list[KnowledgeDocumentSummary], "The selected documents"],
        t: LocaleHandler,
        counted: Annotated[bool, "False when the documents are only the first of more, so counts would mislead"] = True,
    ) -> list[str]:
        key = "agent.record_extraction.facets"
        found = [
            (key_name, counts)
            for key_name, counts in (
                ("folders", Counter(SelectionFacets._folder(document) for document in documents)),
                ("years", Counter(year for document in documents for year in set(_YEAR.findall(document.path)))),
                ("collections", Counter(SelectionFacets._collection(document) for document in documents)),
            )
            if len(counts) > 1
        ]
        lines = [t(f"{key}.{name}", entries=SelectionFacets._entries(counts, counted)) for name, counts in found]
        return lines if counted or not lines else [*lines, t(f"{key}.first", total=len(documents))]

    @staticmethod
    def sample(
        documents: Annotated[list[KnowledgeDocumentSummary], "The selected documents, in order"],
        size: Annotated[int, "How many documents the sample holds"],
    ) -> list[KnowledgeDocumentSummary]:
        """The first document of each of the largest folders, then evenly spread ones, in the selection's order."""
        largest = [folder for folder, _ in Counter(map(SelectionFacets._folder, documents)).most_common(size)]
        chosen = [next(doc for doc in documents if SelectionFacets._folder(doc) == folder) for folder in largest]
        step = max(1, len(documents) // size)
        chosen.extend(doc for doc in documents[::step] if doc not in chosen)
        picked = {id(document) for document in chosen[:size]}
        return [document for document in documents if id(document) in picked]

    @staticmethod
    def _folder(document: KnowledgeDocumentSummary) -> str:
        return document.path.rsplit("/", 1)[0] if "/" in document.path else "/"

    @staticmethod
    def _collection(document: KnowledgeDocumentSummary) -> str:
        return f"{document.collection.bucket_name}/{document.collection.namespace_name}"

    @staticmethod
    def _entries(counts: Counter[str], counted: bool) -> str:
        if counted:
            entries = [f"{name} ({count})" for name, count in counts.most_common(MAX_ENTRIES)]
        else:
            entries = sorted(counts)[:MAX_ENTRIES]
        if len(counts) > MAX_ENTRIES:
            entries.append("…")
        return ", ".join(entries)
