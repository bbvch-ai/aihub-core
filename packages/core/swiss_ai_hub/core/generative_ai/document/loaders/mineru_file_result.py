from pydantic import BaseModel


class MineruFileResult(BaseModel):
    """Extracted per-file fields from one or more /file_parse responses."""

    backend: str
    version: str
    md_content: str
    num_pages: int
    images: dict[str, str]
