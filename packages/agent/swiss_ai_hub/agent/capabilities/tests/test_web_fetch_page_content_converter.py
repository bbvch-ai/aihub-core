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


HEADLINES = [
    "Parliament passes the budget",
    "Storm closes mountain passes",
    "Central bank holds rates",
    "Hospital opens a new wing",
    "Home side wins the derby",
    "Museum returns stolen paintings",
    "Night trains return to the Alps",
    "City plants a thousand trees",
]
STORIES = "".join(
    f'<section><header><h3><a href="/story/{number}">{headline}</a></h3></header>'
    f"<span>What happened, who is affected and what comes next, in our reporters' summary.</span></section>"
    for number, headline in enumerate(HEADLINES)
)
# Shaped like srf.ch/news, where article detection kept the login notice and dropped every headline.
FRONT_PAGE = f"""
<html><head><title>News</title></head><body>
<noscript>Some parts of this site only work with JavaScript.</noscript>
<header><nav><a href="/">Home</a> <a href="/sport">Sport</a> <a href="/weather">Weather</a></nav></header>
<main>
  <section><h2>Your account</h2><p>Log in to comment and personalise your news.</p></section>
  {STORIES}
</main>
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

    async def test_reads_a_short_page_written_without_spaces(self):
        """Chinese and Japanese leave no spaces between words, so a whole paragraph would count as one word."""
        html = "<html><body><h1>通知</h1><p>本周六上午九点至十二点，系统将进行例行维护，暂停服务。</p></body></html>"

        page = await convert(html)

        assert isinstance(page, FetchedWebPage)
        assert "例行维护" in page.markdown

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
class TestPageListingManyStories:
    async def test_reads_every_headline(self):
        """Article detection keeps one block of a front page, which held a login notice instead of the news."""
        page = await convert(FRONT_PAGE, title="News")

        assert isinstance(page, FetchedWebPage)
        assert all(headline in page.markdown for headline in HEADLINES)

    async def test_leaves_the_menus_out(self):
        page = await convert(FRONT_PAGE, title="News")

        assert "Weather" not in page.markdown

    async def test_leaves_out_what_only_a_browser_without_scripts_shows(self):
        """srf.ch/news opened with its notice that the site needs JavaScript, which the reader never saw."""
        page = await convert(FRONT_PAGE, title="News")

        assert "only work with JavaScript" not in page.markdown

    async def test_reads_a_page_wrapped_in_a_form(self):
        """ASP.NET sites such as chinhphu.vn put the whole page inside one form."""
        html = FRONT_PAGE.replace("<body>", "<body><form>").replace("</body>", "</form></body>")

        page = await convert(html, title="News")

        assert all(headline in page.markdown for headline in HEADLINES)


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
