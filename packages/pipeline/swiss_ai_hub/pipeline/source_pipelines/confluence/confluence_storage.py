import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag
from markdownify import ATX, MarkdownConverter
from swiss_ai_hub.core.generative_ai import HtmlTableConverter

_CONVERTER = MarkdownConverter(
    heading_style=ATX,
    bullets="-",
    escape_underscores=False,
    escape_asterisks=False,
    code_language_callback=lambda pre: pre.get("data-language") or "",
)
_CODE_MACROS = {"code", "noformat"}
_DROPPED = ["ac:image", "img", "ac:emoticon", "ac:placeholder", "ri:attachment"]
_UNWRAPPED = ["ac:layout", "ac:layout-section", "ac:layout-cell", "ac:inline-comment-marker", "ac:adf-fallback"]
_TABLE_MARKER = "CONFLUENCETABLE{}"
_TABLE_MARKERS = re.compile(_TABLE_MARKER.format(r"(\d+)"))


class ConfluenceStorage:
    """Turns a page body in Confluence's storage format into markdown.

    Storage format is the one body format Cloud and Data Center share, and the issue asks for it rather than the
    rendered view, which expands every macro server-side. It is XHTML plus ``ac:``/``ri:`` elements for macros, links
    and task lists, which markdownify does not know, so they are rewritten into plain HTML first.
    """

    @classmethod
    def to_markdown(cls, storage: str | None, site: str) -> str:
        """Images and attachments are dropped, since neither is synced. Macros that only render something elsewhere
        (a table of contents, child pages, Jira issues) are dropped too; a macro with a body keeps the body. Plain
        ``_`` and ``*`` stay unescaped, so an identifier such as ``ENG_CONFIG_PATH`` is indexed and found as written.

        Tables go through the converter MinerU's output uses, which wraps them in ``<table>`` tags: the table refiner
        and the chunker recognise a table only by that wrapper, and would otherwise split it like running text.
        """
        if not storage or not storage.strip():
            return ""
        soup = BeautifulSoup(storage, "html.parser")
        for name in _DROPPED:
            for element in soup.find_all(name):
                element.decompose()
        cls._keep_adf_fallbacks(soup)
        cls._rewrite_macros(soup)
        cls._rewrite_task_lists(soup)
        cls._rewrite_links(soup, site)
        for name in _UNWRAPPED:
            for element in soup.find_all(name):
                element.unwrap()
        for moment in soup.find_all("time"):
            cls._replace_with_text(moment, str(moment.get("datetime") or moment.get_text()))
        tables = cls._take_tables(soup)
        markdown = _TABLE_MARKERS.sub(lambda marker: tables[int(marker.group(1))], _CONVERTER.convert_soup(soup))
        return markdown.replace("\xa0", " ").strip()

    @staticmethod
    def _keep_adf_fallbacks(soup: BeautifulSoup) -> None:
        """Cloud stores newer elements (decision lists, some panels) as ADF with an HTML fallback beside it."""
        for extension in soup.find_all("ac:adf-extension"):
            fallback = extension.find("ac:adf-fallback")
            if fallback is None:
                extension.decompose()
            else:
                extension.replace_with(fallback)

    @classmethod
    def _rewrite_macros(cls, soup: BeautifulSoup) -> None:
        """Each lookup takes the first macro left. A macro inside a body that was kept is found by a later lookup,
        because the body is moved into the page, not copied."""
        while (macro := soup.find("ac:structured-macro")) is not None:
            name = macro.get("ac:name", "")
            body = macro.find("ac:rich-text-body", recursive=False)
            if name in _CODE_MACROS:
                macro.replace_with(cls._code_block(soup, macro))
            elif name == "status":
                cls._replace_with_text(macro, cls._parameter(macro, "title"))
            elif body is not None:
                cls._keep_body(soup, macro, body)
            else:
                macro.decompose()

    @classmethod
    def _code_block(cls, soup: BeautifulSoup, macro: Tag) -> Tag:
        body = macro.find("ac:plain-text-body", recursive=False)
        pre = soup.new_tag("pre", attrs={"data-language": cls._parameter(macro, "language")})
        if body is not None:
            pre.string = body.get_text()
        return pre

    @classmethod
    def _keep_body(cls, soup: BeautifulSoup, macro: Tag, body: Tag) -> None:
        """A panel's or an expand's title is the reader's way into its body, so it stays as a bold line above it."""
        if title := cls._parameter(macro, "title"):
            strong = soup.new_tag("strong")
            strong.string = title
            heading = soup.new_tag("p")
            heading.append(strong)
            macro.insert_before(heading)
        macro.replace_with(*body.contents)

    @staticmethod
    def _replace_with_text(element: Tag, text: str) -> None:
        """An element with no text is removed, not replaced by an empty string: markdownify strips the whitespace on
        both sides of an empty string and would glue the neighbouring words together."""
        if text:
            element.replace_with(text)
        else:
            element.decompose()

    @staticmethod
    def _parameter(macro: Tag, name: str) -> str:
        parameter = macro.find("ac:parameter", attrs={"ac:name": name}, recursive=False)
        if parameter is not None:
            return parameter.get_text().strip()
        return ""

    @staticmethod
    def _rewrite_task_lists(soup: BeautifulSoup) -> None:
        for task_list in soup.find_all("ac:task-list"):
            items = soup.new_tag("ul")
            for task in task_list.find_all("ac:task", recursive=False):
                status = task.find("ac:task-status")
                done = status is not None and status.get_text().strip() == "complete"
                item = soup.new_tag("li")
                item.append(f"[{'x' if done else ' '}] ")
                body = task.find("ac:task-body")
                item.extend(list(body.contents) if body is not None else [])
                items.append(item)
            task_list.replace_with(items)

    @classmethod
    def _rewrite_links(cls, soup: BeautifulSoup, site: str) -> None:
        """A link to another page keeps its text only: storage format names the page by title, not by an address the
        file could link to. A user mention without text is dropped rather than written as an account ID."""
        for link in soup.find_all("ac:link"):
            text = cls._link_text(link)
            url = link.find("ri:url")
            address = str(url.get("ri:value") or "") if url is not None else ""
            if address:
                anchor = soup.new_tag("a", attrs={"href": address})
                anchor.string = text or address
                link.replace_with(anchor)
            else:
                cls._replace_with_text(link, text)
        for anchor in soup.find_all("a", href=True):
            anchor["href"] = urljoin(f"{site}/", str(anchor["href"]))

    @staticmethod
    def _link_text(link: Tag) -> str:
        body = link.find(["ac:link-body", "ac:plain-text-link-body"])
        if body is not None:
            return body.get_text()
        target = link.find(["ri:page", "ri:blog-post", "ri:space"])
        if target is not None:
            return str(target.get("ri:content-title", ""))
        return ""

    @staticmethod
    def _take_tables(soup: BeautifulSoup) -> list[str]:
        """Each outermost table, converted on its own and replaced by a marker, because markdownify would otherwise
        turn the converter's ``<table>`` wrapper back into a table of its own. A table nested in a cell is read as
        that cell's text."""
        tables: list[str] = []
        outermost = [table for table in soup.find_all("table") if table.find_parent("table") is None]
        for table in outermost:
            for colgroup in table.find_all("colgroup"):
                colgroup.decompose()
            for nested in table.find_all("table"):
                nested.replace_with(nested.get_text(" ", strip=True))
            table.attrs = {}
            converted = HtmlTableConverter.convert(str(table))
            marker = soup.new_tag("p")
            marker.string = _TABLE_MARKER.format(len(tables))
            table.replace_with(marker)
            tables.append(converted)
        return tables
