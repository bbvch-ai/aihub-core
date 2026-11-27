import asyncio

import trafilatura
from swiss_ai_hub.core.events.agent import WebFetchFailure, WebFetchFailureReason
from trafilatura.settings import use_config
from trafilatura.utils import load_html

from swiss_ai_hub.agent.capabilities.web_fetch.fetched_web_page import FetchedWebPage

# Trafilatura discards an extraction under 250 characters and falls back to flattened text, losing headings,
# tables and links. A short page is still worth reading as markdown, and emptiness is judged below instead.
EXTRACTION_CONFIG = use_config()
EXTRACTION_CONFIG.set("DEFAULT", "MIN_EXTRACTED_SIZE", "0")

# Only catches pages that yielded essentially nothing (a script shell, a bare login form). No length separates a
# paywall teaser from a short real page such as example.com (15 words), so teasers are left to the answer prompt.
# Counted in characters, about five words' worth, because Chinese and Japanese leave no spaces between words.
MIN_CONTENT_CHARACTERS = 25

# Article detection keeps the one block it takes for the article. On a page listing many, such as a news front page,
# that is a single teaser or a login notice (srf.ch/news: 188 of 25,000 characters); articles keep a fifth or more.
MIN_ARTICLE_SHARE = 0.1

# What a page read whole leaves out: its menus, banner and search, dialogs such as consent prompts, and the notices a
# browser running scripts never shows. A header inside an article or section stays, as on a front page it holds a
# headline, and so do forms: ASP.NET wraps the whole page in one.
NON_CONTENT_XPATH = (
    ".//nav|.//dialog|.//noscript|.//*[@role='navigation' or @role='banner' or @role='search' or @role='dialog']"
    "|.//header[not(ancestor::article or ancestor::main or ancestor::section)]"
)


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
        if len("".join(markdown.split())) < MIN_CONTENT_CHARACTERS:
            return WebFetchFailure(url=url, reason=WebFetchFailureReason.EMPTY_CONTENT)
        truncated = len(markdown) > max_characters
        return FetchedWebPage(
            url=url,
            title=title.strip() or None,
            markdown=cls._truncate(markdown, max_characters) if truncated else markdown,
            truncated=truncated,
        )

    @classmethod
    def _extract(cls, html: str, final_url: str) -> str:
        """Falls back to the page's plain text when article detection finds next to nothing of it: no main content
        on pages that are not articles at all (a status page, a single paragraph), one teaser on pages listing many."""
        article = (
            trafilatura.extract(
                html,
                url=final_url,
                output_format="markdown",
                include_links=True,
                include_tables=True,
                include_comments=False,
                favor_recall=True,
                config=EXTRACTION_CONFIG,
            )
            or ""
        )
        page_text = cls._page_text(html)
        return page_text if len(article) < MIN_ARTICLE_SHARE * len(page_text) else article

    @staticmethod
    def _page_text(html: str) -> str:
        """The page's text without its menus, banners and dialogs, flattened: headings, tables and links are lost."""
        tree = load_html(html)
        if tree is None:
            return ""
        for element in tree.xpath(NON_CONTENT_XPATH):
            element.drop_tree()
        return trafilatura.html2txt(tree)

    @staticmethod
    def _truncate(markdown: str, max_characters: int) -> str:
        """Cuts at the last paragraph break that keeps at least half the budget, so the page does not end
        mid-sentence."""
        paragraph_end = markdown.rfind("\n\n", 0, max_characters)
        return markdown[: paragraph_end if paragraph_end >= max_characters // 2 else max_characters]
