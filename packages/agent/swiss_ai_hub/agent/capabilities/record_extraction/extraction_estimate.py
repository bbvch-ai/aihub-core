import math
from typing import Annotated

from swiss_ai_hub.core.generative_ai import KnowledgeDocumentSummary

# One window of the extraction model holds about this many pages of ordinary text.
PAGES_PER_WINDOW = 5
# Spreadsheets, text files and mails report no useful page count (the parser writes 1 or nothing), so their size is
# unknown until loaded; they count as a few windows rather than one, so a batch of them is not underestimated.
UNKNOWN_SIZE_WINDOWS = 2
_PAGES_UNKNOWN = {"csv", "eml", "json", "md", "txt", "xls", "xlsx"}
# One extraction call of a mid-sized model behind the gateway, as measured on the development stack (5–15 s).
SECONDS_PER_WINDOW = 10


class ExtractionEstimate:
    """How long extracting a set of documents takes, roughly, before any of them is loaded.

    Only the page count is known from a listing, so the estimate is coarse and the answer says "about" when it names
    minutes. Extraction calls run in parallel up to the profile's limit.
    """

    @staticmethod
    def windows(document: Annotated[KnowledgeDocumentSummary, "A listed document"]) -> int:
        if document.number_of_pages is None or document.file_type in _PAGES_UNKNOWN:
            return UNKNOWN_SIZE_WINDOWS
        return max(1, math.ceil(document.number_of_pages / PAGES_PER_WINDOW))

    @staticmethod
    def minutes(
        documents: Annotated[list[KnowledgeDocumentSummary], "Documents to extract"],
        parallel: Annotated[int, "Extraction calls one replica makes at once"],
    ) -> int:
        windows = sum(ExtractionEstimate.windows(document) for document in documents)
        return max(1, math.ceil(windows / max(1, parallel) * SECONDS_PER_WINDOW / 60))
