from pathlib import PurePosixPath

from swiss_ai_hub.core.generative_ai.document.parsers.markdown_structural_node_parser import find_markdown_headers


class DocumentTitleDeriver:
    """Derives a document title: email subject, else the first markdown heading, else the filename stem.

    Nothing derived a title before this. Every `document_title` in the platform is the last path segment of the
    source URI, which for `2f8c-invoice-final-v2.pdf` is not what a person would call the document.
    """

    @staticmethod
    def derive(content: str, filename: str, subject: str | None = None) -> str:
        """`subject` wins when present because a mail states its own title; a heading is only an inference."""
        if subject and subject.strip():
            return subject.strip()

        heading = DocumentTitleDeriver._first_heading(content)
        if heading:
            return heading

        return PurePosixPath(filename).stem or filename

    @staticmethod
    def _first_heading(content: str) -> str:
        """The first markdown heading of any level, not the first `#`.

        MinerU labels a scanned document's title by its visual prominence, which is not always level 1 — a page whose
        largest text is rendered as `##` would otherwise fall through to the filename.
        """
        for header in find_markdown_headers(content):
            if header.header_text.strip():
                return header.header_text.strip()
        return ""
