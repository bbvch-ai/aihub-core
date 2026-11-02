import re
from urllib.parse import urljoin
from uuid import uuid4

from bs4 import BeautifulSoup, Comment, Tag
from markdownify import ATX, MarkdownConverter
from swiss_ai_hub.core.generative_ai import HtmlTableConverter

_CONVERTER = MarkdownConverter(heading_style=ATX, bullets="-", escape_underscores=False, escape_asterisks=False)
# Page chrome the parser renders into the content: edit links, the table of contents, navigation boxes, empty
# paragraphs, and the back-links of footnotes.
_DROPPED = [
    ".mw-editsection",
    "#toc",
    ".toc",
    ".navbox",
    ".mw-empty-elt",
    ".mw-cite-backlink",
    "style",
    "script",
    "img",
]
# A template parameter its caller left unset renders as its own name in triple braces.
_UNSET_TEMPLATE_PARAMETER = re.compile(r"\{\{\{[^{}]*\}\}\}")
_BLANK_LINES = re.compile(r"\n{3,}")
_TABLE_MARKER = "MEDIAWIKITABLE{nonce}N{index}"


class MediaWikiHtml:
    """Turns the HTML MediaWiki renders for a page into markdown.

    Rendered HTML is read rather than the stored wikitext, because only the rendered page has every template, magic
    word and extension tag expanded; the wikitext of a page built from an infobox is little more than parameters.
    """

    @classmethod
    def to_markdown(cls, html: str | None, page_url: str) -> str:
        """Links become absolute against the page, because the file is read away from the wiki. Images are dropped:
        an image is a file of its own, synced next to the page when images are synced. Links to pages that do not exist
        keep only their text. Plain ``_`` and ``*`` stay unescaped, so an identifier such as ``ENG_CONFIG_PATH`` is
        indexed and found as written.
        """
        if not html or not html.strip():
            return ""
        soup = BeautifulSoup(html, "html.parser")
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()
        for element in soup.select(", ".join(_DROPPED)):
            element.decompose()
        cls._rewrite_links(soup, page_url)
        cls._unwrap_layout_tables(soup)
        # A marker of this call alone: a page may well contain the text of a fixed one.
        nonce = uuid4().hex
        tables = cls._take_tables(soup, nonce)
        markers = re.compile(_TABLE_MARKER.format(nonce=nonce, index=r"(\d+)"))
        markdown = markers.sub(lambda marker: tables[int(marker.group(1))], _CONVERTER.convert_soup(soup))
        markdown = _UNSET_TEMPLATE_PARAMETER.sub("", markdown).replace("\xa0", " ")
        return _BLANK_LINES.sub("\n\n", markdown).strip()

    @classmethod
    def _unwrap_layout_tables(cls, soup: BeautifulSoup) -> None:
        """Wikis lay pages out with tables: a frame around a process header, a message box, columns side by side.
        Converted as data, such a table puts the whole page into one cell, which the chunker can neither split nor
        read. A table is taken for layout when it holds another table or has a single row, which no data table has,
        and is replaced by its cells' content; a table it held is looked at again once it is outermost."""
        while (table := next(filter(cls._is_layout_table, soup.find_all("table")), None)) is not None:
            cells = [cell for row in cls._rows(table) for cell in row.find_all(["td", "th"], recursive=False)]
            blocks = []
            for cell in cells:
                block = soup.new_tag("div")
                block.extend(list(cell.contents))
                blocks.append(block)
            table.replace_with(*blocks)

    @classmethod
    def _is_layout_table(cls, table: Tag) -> bool:
        return table.find_parent("table") is None and (table.find("table") is not None or len(cls._rows(table)) == 1)

    @staticmethod
    def _rows(table: Tag) -> list[Tag]:
        return [row for row in table.find_all("tr") if row.find_parent("table") is table]

    @staticmethod
    def _take_tables(soup: BeautifulSoup, nonce: str) -> list[str]:
        """Each data table, converted on its own and replaced by a marker, because markdownify would otherwise turn the
        converter's ``<table>`` wrapper back into a table of its own. The table refiner and the chunker recognise a
        table only inside that wrapper, and would otherwise split it like running text. No table holds another one
        here: such a table was layout and is unwrapped already."""
        tables: list[str] = []
        for table in soup.find_all("table"):
            for colgroup in table.find_all("colgroup"):
                colgroup.decompose()
            table.attrs = {}
            converted = HtmlTableConverter.convert(str(table))
            marker = soup.new_tag("p")
            marker.string = _TABLE_MARKER.format(nonce=nonce, index=len(tables))
            table.replace_with(marker)
            tables.append(converted)
        return tables

    @staticmethod
    def _rewrite_links(soup: BeautifulSoup, page_url: str) -> None:
        """A link left without text once its image is gone is removed: markdownify would write it as an empty
        ``[](…)``, which reads as noise in every chunk it lands in. So would the target's title, which MediaWiki puts
        on every link to another page."""
        for link in soup.find_all("a", href=True):
            if not link.get_text(strip=True):
                link.decompose()
            elif "new" in (link.get("class") or []):
                link.replace_with(link.get_text())
            else:
                link["href"] = urljoin(page_url, str(link["href"]))
                del link["title"]
