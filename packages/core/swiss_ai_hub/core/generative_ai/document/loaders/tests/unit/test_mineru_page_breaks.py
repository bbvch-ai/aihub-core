from swiss_ai_hub.core.generative_ai.document.loaders.document_intelligence_loader import PAGE_BREAK
from swiss_ai_hub.core.generative_ai.document.loaders.mineru_page_breaks import MineruPageBreaks


def pages_of(markdown: str) -> list[str]:
    return [page.strip() for page in markdown.split(PAGE_BREAK)]


class TestInsert:
    def test_breaks_go_before_the_first_block_of_each_page(self):
        markdown = "# Title\n\nIntro text.\n\nSecond page text.\n\n<table><tr><td>a</td></tr></table>"
        content_list = [
            {"type": "text", "text": "Title", "text_level": 1, "page_idx": 0},
            {"type": "text", "text": "Intro text.", "page_idx": 0},
            {"type": "page_number", "text": "1", "page_idx": 0},
            {"type": "text", "text": "Second page text.", "page_idx": 1},
            {"type": "table", "table_body": "<table><tr><td>a</td></tr></table>", "page_idx": 2},
        ]

        result = MineruPageBreaks.insert(markdown, content_list, 3)

        assert pages_of(result) == [
            "# Title\n\nIntro text.",
            "Second page text.",
            "<table><tr><td>a</td></tr></table>",
        ]

    def test_a_heading_moves_to_the_page_it_opens_with_its_hashes(self):
        markdown = "First page.\n\n## Chapter 2\n\nBody."
        content_list = [
            {"type": "text", "text": "First page.", "page_idx": 0},
            {"type": "text", "text": "Chapter 2", "text_level": 2, "page_idx": 1},
        ]

        assert pages_of(MineruPageBreaks.insert(markdown, content_list, 2)) == ["First page.", "## Chapter 2\n\nBody."]

    def test_a_page_that_cannot_be_found_keeps_later_pages_numbered(self):
        markdown = "One.\n\nTwo.\n\nThree."
        content_list = [
            {"type": "text", "text": "One.", "page_idx": 0},
            {"type": "text", "text": "Not in the markdown", "page_idx": 1},
            {"type": "text", "text": "Three.", "page_idx": 2},
        ]

        assert pages_of(MineruPageBreaks.insert(markdown, content_list, 3)) == ["One.\n\nTwo.", "", "Three."]

    def test_pages_without_text_still_count(self):
        markdown = "Only page one has text."
        content_list = [{"type": "text", "text": "Only page one has text.", "page_idx": 0}]

        assert MineruPageBreaks.insert(markdown, content_list, 3).count(PAGE_BREAK) == 2

    def test_text_repeated_on_a_later_page_is_found_after_the_earlier_one(self):
        markdown = "Same line.\n\nOther.\n\nSame line."
        content_list = [
            {"type": "text", "text": "Same line.", "page_idx": 0},
            {"type": "text", "text": "Other.", "page_idx": 0},
            {"type": "text", "text": "Same line.", "page_idx": 1},
        ]

        assert pages_of(MineruPageBreaks.insert(markdown, content_list, 2)) == ["Same line.\n\nOther.", "Same line."]

    def test_single_page_is_left_alone(self):
        assert MineruPageBreaks.insert("Text.", [{"type": "text", "text": "Text.", "page_idx": 0}], 1) == "Text."

    def test_without_content_list_all_breaks_go_at_the_end(self):
        assert pages_of(MineruPageBreaks.insert("Text.", [], 2)) == ["Text.", ""]


class TestProbe:
    def test_running_headers_and_page_numbers_are_not_probed(self):
        assert MineruPageBreaks.probe({"type": "header", "text": "Company"}) == ""
        assert MineruPageBreaks.probe({"type": "page_number", "text": "3"}) == ""

    def test_lists_images_and_code_probe_what_the_markdown_shows(self):
        assert MineruPageBreaks.probe({"type": "list", "list_items": ["first item", "second"]}) == "first item"
        assert MineruPageBreaks.probe({"type": "image", "img_path": "images/abc.jpg"}) == "images/abc.jpg"
        assert MineruPageBreaks.probe({"type": "code", "code_body": "def f():\n    pass"}) == "def f():\n    pass"

    def test_long_text_is_cut_to_the_probe_length(self):
        assert len(MineruPageBreaks.probe({"type": "text", "text": "x" * 500})) == MineruPageBreaks.PROBE_LENGTH
