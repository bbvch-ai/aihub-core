from unittest.mock import MagicMock

from swiss_ai_hub.agent.imap.token_budget import TRUNCATION_MARKER, TokenBudget


def _counter(text: str) -> list[int]:
    """One token per four characters — close enough to a real tokenizer to order the trimming decisions."""
    return [0] * (len(text) // 4 + 1)


def test_the_safety_factor_is_applied_so_the_configured_number_is_what_the_model_is_sent():
    """`get_tokenizer()` is not the tokenizer of whichever model LiteLLM routes to, and the chat envelope costs
    tokens of its own — the margin absorbs both."""
    assert TokenBudget(1000, _counter).remaining == 850


def test_reserving_a_fixed_part_takes_it_out_of_the_allowance():
    """A system prompt is sent alongside everything measured here, so a budget ignoring it would promise a bound it
    does not hold."""
    budget = TokenBudget(1000, _counter)
    before = budget.remaining

    budget.reserve("word " * 40)

    assert budget.remaining < before


def test_reserving_nothing_never_pays_for_a_token_count():
    counter = MagicMock(side_effect=_counter)

    TokenBudget(1000, counter).reserve("")

    assert counter.call_count == 0


def test_the_short_circuit_settles_both_extremes_without_a_token_count():
    """Only the band where the estimate cannot decide pays the tokenizer. Once text has to be *trimmed* the sentence
    splitter tokenizes each candidate chunk, and no short-circuit can avoid that."""
    counter = MagicMock(side_effect=_counter)
    budget = TokenBudget(1000, counter)
    remaining = budget.remaining

    assert budget.fits("x" * (remaining // 2)) is True
    assert budget.fits("x" * (remaining * 4 + 1)) is False
    assert counter.call_count == 0

    assert budget.fits("x" * (remaining * 2)) is True
    assert counter.call_count == 1, "the undecidable middle band is exactly what the tokenizer is for"


def test_trimming_keeps_whole_leading_sentences_and_marks_the_cut():
    """Text cut mid-word invites the model to complete the fragment rather than answer it."""
    text = " ".join(f"Sentence number {index} explains the problem." for index in range(200))

    trimmed = TokenBudget(1000, _counter).trim_head(text, room=40)

    assert trimmed.endswith(TRUNCATION_MARKER)
    assert "Sentence number 0 explains the problem." in trimmed
    assert "Sentence number 199 explains the problem." not in trimmed


def test_no_room_at_all_yields_only_the_marker():
    """The caller has already spent the whole allowance on parts that cannot be trimmed; saying so beats emitting a
    fragment that reads like the message."""
    assert TokenBudget(1000, _counter).trim_head("word " * 500, room=0) == TRUNCATION_MARKER
