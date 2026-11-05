import asyncio

import trafilatura
from swiss_ai_hub.core.events.agent import WebFetchFailure, WebFetchFailureReason
from trafilatura.settings import use_config

from swiss_ai_hub.agent.capabilities.web_fetch.fetched_web_page import FetchedWebPage

# Trafilatura discards an extraction under 250 characters and falls back to flattened text, losing headings,
# tables and links. A short page is still worth reading as markdown, and emptiness is judged below instead.
EXTRACTION_CONFIG = use_config()
EXTRACTION_CONFIG.set("DEFAULT", "MIN_EXTRACTED_SIZE", "0")

# Only catches pages that yielded essentially nothing (a script shell, a bare login form). No word count separates
# a paywall teaser from a short real page such as example.com (15 words), so teasers are left to the answer prompt.
MIN_CONTENT_WORDS = 5


class PageContentConverter:
    """Turns a rendered page into the markdown the model reads, keeping the article and dropping menus and
    footers, which would otherwise spend the context budget on navigation links."""

    @classmethod
    async def convert(
        cls, url: str, final_url: str, title: str, html: str, max_characters: int
    ) -> FetchedWebPage | WebFetchFailure:
        """`url` is what the user pasted, so the citation matches the message; `final_url` is where the page
        ended up, so relative links in the markdown resolve against the right site."""
        markdown = await asyncio.to_thread(cls._extract, html, final_url)
        if len(markdown.split()) < MIN_CONTENT_WORDS:
            return WebFetchFailure(url=url, reason=WebFetchFailureReason.EMPTY_CONTENT)
        truncated = len(markdown) > max_characters
        return FetchedWebPage(
            url=url,
            title=title.strip() or None,
            markdown=cls._truncate(markdown, max_characters) if truncated else markdown,
            truncated=truncated,
        )

    @staticmethod
    def _extract(html: str, final_url: str) -> str:
        """Falls back to the page's plain text when article detection finds no main content, which it does for
        pages that are not articles at all: a product listing, a status page, a single paragraph."""
        markdown = trafilatura.extract(
            html,
            url=final_url,
            output_format="markdown",
            include_links=True,
            include_tables=True,
            include_comments=False,
            favor_recall=True,
            config=EXTRACTION_CONFIG,
        )
        return markdown or trafilatura.html2txt(html) or ""

    @staticmethod
    def _truncate(markdown: str, max_characters: int) -> str:
        """Cuts at the last paragraph break that keeps at least half the budget, so the page does not end
        mid-sentence."""
        paragraph_end = markdown.rfind("\n\n", 0, max_characters)
        return markdown[: paragraph_end if paragraph_end >= max_characters // 2 else max_characters]
