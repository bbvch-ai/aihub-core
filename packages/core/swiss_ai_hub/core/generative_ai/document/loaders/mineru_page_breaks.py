from typing import Any, ClassVar

from swiss_ai_hub.core.generative_ai.document.loaders.document_intelligence_loader import PAGE_BREAK


class MineruPageBreaks:
    """Marks where each page starts in MinerU's markdown, which joins all pages without a trace of their boundaries.

    MinerU's content list holds the same blocks as the markdown, in the same order, each with its page. A page
    starts at the first of its blocks found in the markdown, searching onward from the block before, so the marks
    can only move forward. A page none of whose blocks can be found stays with the page before; the next page found
    then gets the breaks of both, so counting the breaks still gives every later page its true number.
    """

    PROBE_LENGTH: ClassVar[int] = 60
    # Running headers, footers and page numbers are left out of MinerU's markdown, so they cannot be found in it.
    DISCARDED_TYPES: ClassVar[frozenset[str]] = frozenset(
        {"header", "footer", "page_number", "aside_text", "page_footnote"}
    )

    @staticmethod
    def insert(markdown: str, content_list: list[dict[str, Any]], number_of_pages: int) -> str:
        """The markdown with `number_of_pages - 1` page breaks, each placed before the page it opens."""
        if number_of_pages <= 1:
            return markdown
        starts = MineruPageBreaks.page_starts(markdown, content_list)
        parts: list[str] = []
        previous_offset, previous_page = 0, 0
        for page, offset in sorted(starts.items()):
            if page == 0 or page >= number_of_pages:
                continue
            parts.append(markdown[previous_offset:offset].rstrip("\n"))
            parts.extend([PAGE_BREAK] * (page - previous_page))
            previous_offset, previous_page = offset, page
        parts.append(markdown[previous_offset:])
        parts.extend([PAGE_BREAK] * (number_of_pages - 1 - previous_page))
        return "\n\n".join(part for part in parts if part)

    @staticmethod
    def page_starts(markdown: str, content_list: list[dict[str, Any]]) -> dict[int, int]:
        """Each page found, by its index in the batch, to the offset of the line its first block starts on."""
        starts: dict[int, int] = {}
        cursor = 0
        for block in content_list:
            probe = MineruPageBreaks.probe(block)
            if not probe:
                continue
            found = markdown.find(probe, cursor)
            if found < 0:
                continue
            page = block.get("page_idx", 0)
            if page not in starts:
                starts[page] = markdown.rfind("\n", cursor, found) + 1 or cursor
            cursor = found + len(probe)
        return starts

    @staticmethod
    def probe(block: dict[str, Any]) -> str:
        """The start of a block's text as the markdown spells it; empty for a block the markdown leaves out."""
        match block.get("type"):
            case kind if kind in MineruPageBreaks.DISCARDED_TYPES:
                return ""
            case "list":
                text = next(iter(block.get("list_items") or []), "")
            case "table":
                text = block.get("table_body") or next(iter(block.get("table_caption") or []), "")
            case "image":
                text = block.get("img_path", "")
            case "code":
                text = block.get("code_body", "")
            case _:
                text = block.get("text", "")
        return text.strip()[: MineruPageBreaks.PROBE_LENGTH]
