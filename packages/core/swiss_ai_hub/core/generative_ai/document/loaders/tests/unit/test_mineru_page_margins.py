from swiss_ai_hub.core.generative_ai.document.loaders.document_intelligence_loader import PAGE_BREAK
from swiss_ai_hub.core.generative_ai.document.loaders.mineru_page_breaks import MineruPageBreaks
from swiss_ai_hub.core.generative_ai.document.loaders.mineru_page_margins import MineruPageMargins


def pages_of(markdown: str) -> list[str]:
    return [page.strip() for page in markdown.split(PAGE_BREAK)]


class TestRestore:
    def test_a_letterhead_goes_above_the_page_and_the_bank_details_below(self):
        """A real invoice (Mustang 501): MinerU dropped the sender, so a request by supplier never found it."""
        content_list = [
            {"type": "text", "text": "Rechnung # RE-20140522/501 vom 22.05.2014", "page_idx": 0},
            {"type": "header", "text": "#", "page_idx": 0},
            {"type": "header", "text": "Bei Spiel GmbH", "page_idx": 0},
            {"type": "footer", "text": "IBAN DE88 2008 0000 0970 3757 00", "page_idx": 0},
        ]

        result = MineruPageMargins.restore("Rechnung # RE-20140522/501 vom 22.05.2014", content_list)

        assert (
            result == "Bei Spiel GmbH\n\nRechnung # RE-20140522/501 vom 22.05.2014\n\nIBAN DE88 2008 0000 0970 3757 00"
        )

    def test_each_margin_stays_on_its_own_page(self):
        content_list = [
            {"type": "text", "text": "First.", "page_idx": 0},
            {"type": "text", "text": "Second.", "page_idx": 1},
            {"type": "header", "text": "Invoice no 42", "page_idx": 1},
            {"type": "footer", "text": "Thank you", "page_idx": 0},
        ]
        markdown = MineruPageBreaks.insert("First.\n\nSecond.", content_list, 2)

        result = MineruPageMargins.restore(markdown, content_list)

        assert pages_of(result) == ["First.\n\nThank you", "Invoice no 42\n\nSecond."]

    def test_a_running_header_is_restored_once(self):
        content_list = [
            {"type": "header", "text": "ACME AG  Annual report", "page_idx": 0},
            {"type": "text", "text": "One.", "page_idx": 0},
            {"type": "header", "text": "ACME AG Annual report", "page_idx": 1},
            {"type": "text", "text": "Two.", "page_idx": 1},
        ]
        markdown = MineruPageBreaks.insert("One.\n\nTwo.", content_list, 2)

        result = MineruPageMargins.restore(markdown, content_list)

        assert pages_of(result) == ["ACME AG  Annual report\n\nOne.", "Two."]

    def test_page_numbers_and_side_notes_stay_out(self):
        content_list = [
            {"type": "text", "text": "Body.", "page_idx": 0},
            {"type": "page_number", "text": "1", "page_idx": 0},
            {"type": "aside_text", "text": "Draft", "page_idx": 0},
            {"type": "page_footnote", "text": "1 See annex.", "page_idx": 0},
        ]

        assert MineruPageMargins.restore("Body.", content_list) == "Body."

    def test_a_page_without_margins_is_left_as_it_is(self):
        content_list = [
            {"type": "text", "text": "One.", "page_idx": 0},
            {"type": "header", "text": "Seller GmbH", "page_idx": 0},
            {"type": "text", "text": "Two.", "page_idx": 1},
        ]
        markdown = MineruPageBreaks.insert("One.\n\nTwo.", content_list, 2)

        result = MineruPageMargins.restore(markdown, content_list)

        assert result.split(PAGE_BREAK)[1] == markdown.split(PAGE_BREAK)[1]
        assert pages_of(result) == ["Seller GmbH\n\nOne.", "Two."]

    def test_an_image_gets_its_header_on_top(self):
        """The donut invoice images: MinerU typed "Invoice no / Date of issue" as a header on all of them."""
        content_list = [
            {"type": "header", "text": "Invoice no: 51109338 Date of issue: 04/13/2013", "page_idx": 0},
            {"type": "text", "text": "Seller: Andrews, Kirby and Valdez", "page_idx": 0},
        ]

        result = MineruPageMargins.restore("Seller: Andrews, Kirby and Valdez", content_list)

        assert result.startswith("Invoice no: 51109338 Date of issue: 04/13/2013\n\nSeller:")

    def test_a_block_numbered_past_the_last_page_goes_on_the_last_page(self):
        content_list = [{"type": "footer", "text": "Seller GmbH", "page_idx": 5}]

        assert MineruPageMargins.restore("Body.", content_list) == "Body.\n\nSeller GmbH"

    def test_nothing_to_restore_returns_the_markdown_unchanged(self):
        markdown = f"One.\n\n{PAGE_BREAK}\n\nTwo."

        assert MineruPageMargins.restore(markdown, []) is markdown
