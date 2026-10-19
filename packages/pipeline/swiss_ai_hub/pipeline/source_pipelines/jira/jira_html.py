from urllib.parse import urljoin

from bs4 import BeautifulSoup
from markdownify import ATX, MarkdownConverter

_CONVERTER = MarkdownConverter(heading_style=ATX, bullets="-", escape_underscores=False, escape_asterisks=False)


class JiraHtml:
    """Turns the HTML Jira renders for a description or a comment into markdown.

    Rendered HTML is the one text format Cloud and Data Center share; their raw formats differ (ADF on Cloud v3, wiki
    markup elsewhere).
    """

    @staticmethod
    def to_markdown(html: str | None, site: str) -> str:
        """Links become absolute, because the file is read away from Jira. Images are dropped, since attachments
        are not synced, and user mentions keep only the name, not the account id their profile link carries.

        Jira's relative links already start with its context path (``/jira/browse/…``), so they are resolved against
        the site rather than appended to it. Data Center renders ``{{monospace}}`` as ``<tt>``, which markdownify
        would flatten into plain text. Plain ``_`` and ``*`` stay unescaped, so an identifier such as
        ``ENG_CONFIG_PATH`` is indexed and found as written.
        """
        if not html or not html.strip():
            return ""
        soup = BeautifulSoup(html, "html.parser")
        for monospace in soup.find_all("tt"):
            monospace.name = "code"
        for image in soup.find_all("img"):
            image.decompose()
        for mention in soup.select("a.user-hover"):
            mention.replace_with(mention.get_text())
        for link in soup.find_all("a", href=True):
            link["href"] = urljoin(f"{site}/", link["href"])
        return _CONVERTER.convert_soup(soup).strip()
