from enum import StrEnum

from pydantic import BaseModel

_KIB = 1024


class AttachmentOutcome(StrEnum):
    """What reading one attachment produced.

    Three outcomes rather than success/failure, because "we read it and it holds no text" is a real and common answer
    — a photo, a scanned page OCR could not resolve — and it is not an error. The distinction is what decides whether
    a text block reaches the prompt, while all three still reach the inventory.
    """

    TEXT = "text"
    NO_TEXT = "no_text"
    UNREADABLE = "unreadable"


class ExtractedAttachment(BaseModel):
    """One attachment as the drafting prompt sees it: what it was, and whatever text came out of it.

    Carries the outcome rather than an empty string for the textless case, so the prompt builder can say *why* there
    is no text instead of silently omitting the attachment. A sender who wrote "see attached" and got a reply that
    ignored the attachment is the failure this prevents.
    """

    filename: str
    content_type: str
    size_bytes: int
    outcome: AttachmentOutcome
    text: str = ""
    detail: str = ""

    @property
    def inventory_line(self) -> str:
        """One line naming the attachment and what came of reading it — always present, for every outcome."""
        size = f"{round(self.size_bytes / _KIB)} KB" if self.size_bytes >= _KIB else f"{self.size_bytes} B"
        described = f"{self.filename} ({self.content_type}, {size})"
        if self.outcome is AttachmentOutcome.TEXT:
            return described
        return f"{described} — {self.detail}"
