"""Tests for converting parser-emitted HTML tables into markdown."""

from swiss_ai_hub.core.generative_ai.document.tables.html_table_converter import HtmlTableConverter
from swiss_ai_hub.core.generative_ai.document.tables.markdown_table import parse_markdown_table

# Shape MinerU actually emits: no <th>, no pipes, spans on the header cells.
MINERU_TABLE = (
    "<table>"
    '<tr><td rowspan="2">Erwerbseinkommen</td><td colspan="2">Beitrag</td></tr>'
    "<tr><td>Jahr</td><td>Monat</td></tr>"
    "<tr><td>9 800</td><td>474.80</td><td>39.55</td></tr>"
    "<tr><td>9 900</td><td>479.60</td><td>39.95</td></tr>"
    "</table>"
)


class TestHtmlTableConverter:
    def test_mineru_html_table_becomes_parseable_markdown(self) -> None:
        result = HtmlTableConverter.convert(MINERU_TABLE)

        assert "<tr>" not in result
        assert result.startswith("<table>")
        assert result.endswith("</table>")

        df = parse_markdown_table(result.removeprefix("<table>").removesuffix("</table>"))
        assert df is not None
        assert len(df) == 3

    def test_spanned_cells_are_expanded_into_every_column(self) -> None:
        result = HtmlTableConverter.convert(MINERU_TABLE)

        assert result.count("Erwerbseinkommen") >= 2

    def test_no_padding_is_introduced(self) -> None:
        """to_markdown pads cells to column width, which inflated a real document ~36x."""
        result = HtmlTableConverter.convert(MINERU_TABLE)

        assert "  |" not in result

    def test_markdown_table_is_left_untouched(self) -> None:
        markdown = "<table>| A | B |\n|---|---|\n| 1 | 2 |</table>"

        assert HtmlTableConverter.convert(markdown) == markdown

    def test_unparseable_table_is_left_untouched(self) -> None:
        text = "<table>This is not a valid table structure</table>"

        assert HtmlTableConverter.convert(text) == text

    def test_empty_table_is_left_untouched(self) -> None:
        text = "<table></table>"

        assert HtmlTableConverter.convert(text) == text

    def test_surrounding_content_is_preserved(self) -> None:
        text = f"# Heading\n\nintro\n\n{MINERU_TABLE}\n\noutro"
        result = HtmlTableConverter.convert(text)

        assert "# Heading" in result
        assert "intro" in result
        assert "outro" in result

    def test_multiple_tables_are_all_converted(self) -> None:
        result = HtmlTableConverter.convert(f"{MINERU_TABLE}\n\n{MINERU_TABLE}")

        assert result.count("<table>") == 2
        assert "<tr>" not in result

    def test_cells_containing_pipes_do_not_break_the_table(self) -> None:
        html = "<table><tr><td>A</td><td>B</td></tr><tr><td>x|y</td><td>2</td></tr></table>"

        result = HtmlTableConverter.convert(html)
        df = parse_markdown_table(result.removeprefix("<table>").removesuffix("</table>"))

        assert df is not None
        assert len(df) == 1

    def test_cells_containing_newlines_stay_on_one_row(self) -> None:
        html = "<table><tr><td>A</td><td>B</td></tr><tr><td>x<br>y</td><td>2</td></tr></table>"

        result = HtmlTableConverter.convert(html)
        df = parse_markdown_table(result.removeprefix("<table>").removesuffix("</table>"))

        assert df is not None
        assert len(df) == 1


class TestConversionComposesWithMarkdownWrapping:
    """
    MineruLoader runs wrap_markdown_tables and the converter back to back.

    The converter emits a bare pipe table inside <table> tags, which is exactly what wrap_markdown_tables
    looks for, so running it after the converter wraps every table a second time. Only a real document
    exposed this — the nesting is invisible to a tag count and downstream parsers happen to tolerate it.
    """

    @staticmethod
    def loader_pipeline(markdown_content: str) -> str:
        from swiss_ai_hub.core.generative_ai.document.tables.markdown_table import wrap_markdown_tables

        return HtmlTableConverter.convert(wrap_markdown_tables(markdown_content))

    def test_html_table_is_wrapped_exactly_once(self) -> None:
        result = self.loader_pipeline(MINERU_TABLE)

        assert result.count("<table>") == 1
        assert result.count("</table>") == 1

    def test_bare_markdown_table_is_wrapped_exactly_once(self) -> None:
        result = self.loader_pipeline("| A | B |\n|---|---|\n| 1 | 2 |")

        assert result.count("<table>") == 1
        assert result.count("</table>") == 1

    def test_mixed_document_wraps_each_table_once(self) -> None:
        result = self.loader_pipeline(f"{MINERU_TABLE}\n\ntext\n\n| A | B |\n|---|---|\n| 1 | 2 |")

        assert result.count("<table>") == 2
        assert result.count("</table>") == 2


class TestEmptyCellsAreNotRenderedAsPlaceholders:
    """pd.read_html yields NaN for merged or empty cells; rendering those embeds the literal string "nan"."""

    def test_empty_cells_render_blank(self) -> None:
        html = (
            "<table>"
            "<tr><td></td><td></td><td>Franken</td></tr>"
            "<tr><td>bis</td><td>15 200 Franken</td><td>0.00</td></tr>"
            "<tr><td></td><td>je weitere 100 Franken</td><td>0.77</td></tr>"
            "</table>"
        )

        result = HtmlTableConverter.convert(html)

        assert "nan" not in result.lower()
        assert "Franken" in result

    def test_row_structure_survives_blanking(self) -> None:
        html = "<table><tr><td>A</td><td></td></tr><tr><td>1</td><td></td></tr></table>"

        result = HtmlTableConverter.convert(html)
        df = parse_markdown_table(result.removeprefix("<table>").removesuffix("</table>"))

        assert df is not None
        assert len(df) == 1
