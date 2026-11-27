"""Figure descriptions decide per run whether to work, and with which model."""

from unittest.mock import MagicMock, Mock, patch

from dagster import build_op_context

from swiss_ai_hub.pipeline.ops.data_lake.generate_figure_descriptions import generate_figure_descriptions
from swiss_ai_hub.pipeline.types.ref_doc_document import RefDocDocument

_MODULE = "swiss_ai_hub.pipeline.ops.data_lake.generate_figure_descriptions"
_PARTITION = "contracts|s3:%2F%2Fcontracts%2Fa.pdf"
_F1 = "<figure>![Figure 1](s3://contracts/__figures__/1.png)</figure>"
_F2 = "<figure>![Figure 2](s3://contracts/__figures__/2.png)</figure>"


class TestGenerateFigureDescriptions:
    def test_a_database_that_opted_out_gets_its_document_back_without_a_model_call(self):
        ref_doc = RefDocDocument(text="<figure>![](s3://contracts/fig.png)</figure>", id_="doc", metadata={})
        with (
            patch(f"{_MODULE}.ingestor_config_for_bucket", return_value=Mock(with_figure_descriptions=False)),
            patch(f"{_MODULE}.build_vision_model") as build_vision_model,
        ):
            result = generate_figure_descriptions(
                build_op_context(partition_key=_PARTITION, resources={"data_lake_file_system": Mock()}),
                ref_doc,
            )

        build_vision_model.assert_not_called()
        assert result is ref_doc

    def test_a_database_that_opted_in_describes_with_its_vision_model(self):
        """#1819: the vision model is resolved per database, falling back to its text model inside the resolver."""
        ref_doc = RefDocDocument(text="no figures here", id_="doc", metadata={})
        with (
            patch(f"{_MODULE}.ingestor_config_for_bucket", return_value=Mock(with_figure_descriptions=True)),
            patch(f"{_MODULE}.build_vision_model") as build_vision_model,
        ):
            generate_figure_descriptions(
                build_op_context(partition_key=_PARTITION, resources={"data_lake_file_system": Mock()}),
                ref_doc,
            )

        build_vision_model.assert_called_once_with("contracts")


def _describe(text: str, descriptions: list[str] | None = None) -> tuple[RefDocDocument, list[tuple[str, str]]]:
    """Runs the op on `text` and returns the result with each vision call's (before, after) context."""
    file_system = MagicMock()
    file_system.open.return_value.__enter__.return_value.read.return_value = b"png"
    with (
        patch(f"{_MODULE}.ingestor_config_for_bucket", return_value=Mock(with_figure_descriptions=True)),
        patch(f"{_MODULE}.build_vision_model"),
        patch(
            f"{_MODULE}.generate_description",
            side_effect=descriptions or ["first description", "second description"],
        ) as generate_description,
        build_op_context(partition_key=_PARTITION, resources={"data_lake_file_system": file_system}) as context,
    ):
        result = generate_figure_descriptions(context, RefDocDocument(text=text, id_="doc", metadata={}))
    contexts = [
        (description_call.kwargs["before_text_block"].text, description_call.kwargs["after_text_block"].text)
        for description_call in generate_description.call_args_list
    ]
    return result, contexts


class TestFigureContext:
    """private#493: the context of a figure is the text that belongs to it, never a neighbouring figure or table."""

    def test_two_adjacent_figures_are_described_without_context(self):
        result, contexts = _describe(_F1 + _F2)

        assert contexts == [("", ""), ("", "")]
        assert result.text == (
            "<figure>![first description](s3://contracts/__figures__/1.png)</figure>"
            "<figure>![second description](s3://contracts/__figures__/2.png)</figure>"
        )

    def test_a_blank_line_between_figures_does_not_leak_the_previous_description(self):
        _, contexts = _describe(_F1 + "\n\n" + _F2)

        assert contexts[1][0] == ""

    def test_figures_across_a_page_break_are_described_without_context(self):
        _, contexts = _describe(_F1 + "\n<!-- PageBreak -->\n" + _F2)

        assert contexts == [("", ""), ("", "")]

    def test_a_caption_after_a_page_break_stops_at_the_page_break(self):
        _, contexts = _describe("Page one text.\n<!-- PageBreak -->\nCaption on page 2\n" + _F1)

        assert contexts[0][0] == "Caption on page 2"

    def test_a_figure_next_to_tables_reads_their_cell_text(self):
        first_table = "<table><tr><td>Name</td><td>Value</td></tr></table>"
        second_table = "<table><tr><td>A</td></tr></table>"

        result, contexts = _describe("Intro\n" + first_table + _F1 + second_table)

        assert contexts[0] == ("Intro\n Name Value", "A")
        assert first_table in result.text
        assert second_table in result.text

    def test_a_figure_nested_in_a_neighbouring_tag_is_a_boundary(self):
        _, contexts = _describe("<table><tr><td>" + _F1 + "</td></tr></table>" + _F2)

        assert contexts[1][0] == ""

    def test_an_autolink_does_not_carry_the_next_figure_into_the_context(self):
        """html.parser leaves markdownify's `<https://…>` unclosed, so the rest of the document nests inside it."""
        _, contexts = _describe("Intro\n" + _F1 + "\nSee <https://example.ch> for more\n" + _F2 + "\nend")

        assert contexts[0][1] == "See"

    def test_a_line_break_tag_keeps_words_apart(self):
        _, contexts = _describe("line1<br>line2\n" + _F1)

        assert contexts[0][0].split() == ["line1", "line2"]

    def test_prose_between_figures_is_the_context_of_both(self):
        _, contexts = _describe("Before one.\n" + _F1 + "\nBetween.\n" + _F2 + "\nAfter.")

        assert contexts == [
            ("Before one.", "Between."),
            ("Between.", "After."),
        ]

    def test_the_first_figure_has_no_context_before_it(self):
        _, contexts = _describe(_F1 + "\nAfter.", ["description"])

        assert contexts[0] == ("", "After.")

    def test_the_last_figure_has_no_context_after_it(self):
        _, contexts = _describe("Before.\n" + _F1, ["description"])

        assert contexts[0] == ("Before.", "")

    def test_context_is_capped_on_each_side(self):
        _, contexts = _describe("a" * 2000 + "B" + _F1 + "C" + "d" * 2000, ["description"])

        before, after = contexts[0]
        assert len(before) == 1500
        assert before.endswith("B")
        assert len(after) == 1500
        assert after.startswith("C")

    def test_escaped_characters_survive_the_round_trip(self):
        result, _ = _describe("x < y & z\n" + _F1, ["A & <b>"])

        assert "x < y & z" in result.text
        assert "![A & <b>](s3://contracts/__figures__/1.png)" in result.text
