from swiss_ai_hub.core.generative_ai.structured_extraction.extracted_table_markup import ExtractedTableMarkup


def test_a_marked_table_is_condensed_to_one_line_and_the_rest_stays():
    answer = f"{ExtractedTableMarkup.wrap('| a |\n|---|\n| 1 |', rows=1)}\n\n**Files matched:** 1"

    assert ExtractedTableMarkup.condensed(answer) == (
        "[A table of 1 extracted rows was shown here.]\n\n**Files matched:** 1"
    )


def test_every_marked_table_of_an_answer_is_condensed():
    answer = f"{ExtractedTableMarkup.wrap('| a |', rows=3)}\n\nand\n\n{ExtractedTableMarkup.wrap('| b |', rows=4)}"

    condensed = ExtractedTableMarkup.condensed(answer)

    assert "| a |" not in condensed
    assert "| b |" not in condensed
    assert "3 extracted rows" in condensed
    assert "4 extracted rows" in condensed


def test_a_cell_quoting_a_marker_does_not_end_the_table_early():
    table = "| clause |\n|---|\n| see [/aihub-extracted-table]: # below |\n| last row |"
    answer = f"{ExtractedTableMarkup.wrap(table, rows=2)}\n\n**Files matched:** 1"

    assert ExtractedTableMarkup.condensed(answer) == (
        "[A table of 2 extracted rows was shown here.]\n\n**Files matched:** 1"
    )


def test_text_without_markers_is_unchanged():
    assert ExtractedTableMarkup.condensed("| plain | table |") == "| plain | table |"
