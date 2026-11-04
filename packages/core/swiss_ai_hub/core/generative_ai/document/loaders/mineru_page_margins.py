from typing import Any, ClassVar

from swiss_ai_hub.core.generative_ai.document.loaders.document_intelligence_loader import PAGE_BREAK


class MineruPageMargins:
    """Puts back the page headers and footers MinerU leaves out of its markdown.

    MinerU types a page's top and bottom blocks `header` and `footer` and drops them, but on an invoice or a letter
    they hold the sender, the invoice number, the date and the bank details. Each is restored on its own page, the
    headers above its text and the footers below; a text already restored on an earlier page is not repeated, so a
    running header appears once instead of on every page.
    """

    RESTORED_TYPES: ClassVar[dict[str, str]] = {"header": "above", "footer": "below"}

    @staticmethod
    def restore(markdown: str, content_list: list[dict[str, Any]]) -> str:
        """The markdown, split at its page breaks, with each page's headers and footers around it."""
        pages = markdown.split(PAGE_BREAK)
        above: list[list[str]] = [[] for _ in pages]
        below: list[list[str]] = [[] for _ in pages]
        seen: set[str] = set()
        for block in content_list:
            side = MineruPageMargins.RESTORED_TYPES.get(block.get("type", ""))
            text = (block.get("text") or "").strip()
            key = " ".join(text.split()).casefold()
            if side is None or not any(character.isalnum() for character in text) or key in seen:
                continue
            seen.add(key)
            page = min(max(block.get("page_idx", 0), 0), len(pages) - 1)
            (above if side == "above" else below)[page].append(text)
        if not seen:
            return markdown
        return PAGE_BREAK.join(
            MineruPageMargins._framed(page, above[index], below[index]) for index, page in enumerate(pages)
        )

    @staticmethod
    def _framed(page: str, above: list[str], below: list[str]) -> str:
        if not above and not below:
            return page
        text = page.strip()
        lead = page[: len(page) - len(page.lstrip())]
        trail = page[len(page.rstrip()) :]
        return lead + "\n\n".join(part for part in [*above, text, *below] if part) + trail
