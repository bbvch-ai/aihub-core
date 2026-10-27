import pytest
from swiss_ai_hub.core.events.agent import WebFetchFailure, WebFetchFailureReason

from swiss_ai_hub.agent.capabilities.web_fetch.fetched_web_page import FetchedWebPage
from swiss_ai_hub.agent.capabilities.web_fetch.page_content_converter import PageContentConverter

URL = "https://example.com/pricing"
ARTICLE = """
<html><head><title>Pricing</title></head><body>
<nav><a href="/">Home</a> <a href="/about">About</a> <a href="/careers">Careers</a></nav>
<article>
  <h1>Pricing</h1>
  <p>Our plans are simple and fair. Every plan includes support, updates and unlimited projects for your team.</p>
  <table><tr><th>Plan</th><th>Price</th></tr><tr><td>Pro</td><td>10 CHF</td></tr></table>
  <p>Read the <a href="/docs">documentation</a> for details on billing, invoices and refunds.</p>
</article>
<footer>Copyright 2026 Example AG. Imprint. Privacy policy. Cookie settings.</footer>
</body></html>
"""


async def convert(html: str = ARTICLE, title: str = "Pricing", max_characters: int = 10_000):
    return await PageContentConverter.convert(URL, "https://www.example.com/pricing", title, html, max_characters)


@pytest.mark.asyncio
class TestConversion:
    async def test_keeps_the_article_as_markdown(self):
        page = await convert()

        assert isinstance(page, FetchedWebPage)
        assert "Our plans are simple and fair" in page.markdown
        assert "| Pro | 10 CHF |" in page.markdown

    async def test_drops_navigation_and_footer(self):
        """Menus and footers would spend the context budget on links the model cannot use."""
        page = await convert()

        assert "Careers" not in page.markdown
        assert "Cookie settings" not in page.markdown

    async def test_resolves_relative_links_against_where_the_page_ended_up(self):
        page = await convert()

        assert "https://www.example.com/docs" in page.markdown

    async def test_cites_the_url_the_user_pasted(self):
        """The citation must match what the user sees in their own message, not the redirect target."""
        page = await convert()

        assert page.url == URL

    async def test_reads_a_short_page_that_is_not_an_article(self):
        """example.com has 15 words; article detection rejects it, the plain-text fallback does not."""
        html = (
            "<html><body><h1>Example Domain</h1><p>This domain is for use in documentation examples.</p></body></html>"
        )

        page = await convert(html)

        assert isinstance(page, FetchedWebPage)
        assert "documentation examples" in page.markdown

    @pytest.mark.parametrize(
        "html",
        [
            "<html><body></body></html>",
            "<html><body><div id='root'></div><script>render()</script></body></html>",
            "<html><body><p>Please log in.</p></body></html>",
        ],
    )
    async def test_reports_a_page_that_yielded_nothing(self, html: str):
        result = await convert(html)

        assert result == WebFetchFailure(url=URL, reason=WebFetchFailureReason.EMPTY_CONTENT)


@pytest.mark.asyncio
class TestTitle:
    async def test_strips_the_title(self):
        page = await convert(title="  Pricing  \n")

        assert page.title == "Pricing"

    async def test_leaves_a_missing_title_empty_for_the_citation_to_fall_back_on(self):
        page = await convert(title="   ")

        assert page.title is None


@pytest.mark.asyncio
class TestTruncation:
    async def test_does_not_truncate_what_fits(self):
        page = await convert()

        assert page.truncated is False

    async def test_truncates_to_the_budget_and_says_so(self):
        page = await convert(max_characters=120)

        assert page.truncated is True
        assert len(page.markdown) <= 120


class TestTruncationBoundary:
    def test_cuts_at_a_paragraph_break_when_one_is_close(self):
        markdown = "First paragraph here.\n\nSecond paragraph that runs well past the budget."

        assert PageContentConverter._truncate(markdown, 40) == "First paragraph here."

    def test_cuts_hard_when_the_last_paragraph_break_is_too_early(self):
        """Falling back to a break in the first half would throw away most of the budget."""
        markdown = "Tiny.\n\n" + "x" * 100

        assert PageContentConverter._truncate(markdown, 60) == markdown[:60]
