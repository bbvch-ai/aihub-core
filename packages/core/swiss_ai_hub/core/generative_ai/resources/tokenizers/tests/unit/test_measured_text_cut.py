from swiss_ai_hub.core.generative_ai.resources.tokenizers.measured_text_cut import MeasuredTextCut
from swiss_ai_hub.core.generative_ai.resources.tokenizers.model_tokenizer import ModelTokenizer


def test_head_is_the_longest_prefix_that_measures_within_the_limit() -> None:
    count = ModelTokenizer.shared("bge-m3").count
    text = "Die Kündigungsfrist beträgt dreissig Tage. " * 200

    head = MeasuredTextCut.longest_fitting_head(text, 100, count)

    assert count(head) <= 100
    assert count(text[: len(head) + 40]) > 100


def test_tail_keeps_the_end() -> None:
    count = ModelTokenizer.shared("bge-m3").count
    text = ("filler " * 500) + "the question"

    tail = MeasuredTextCut.longest_fitting_tail(text, 20, count)

    assert tail.endswith("the question")
    assert count(tail) <= 20


def test_pieces_cover_the_text_and_each_fits() -> None:
    count = ModelTokenizer.shared("bge-m3").count
    text = "x" * 100_000

    pieces = MeasuredTextCut.pieces(text, 2048, count)

    assert "".join(pieces) == text
    assert all(count(piece) <= 2048 for piece in pieces)
