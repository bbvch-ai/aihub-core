from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from swiss_ai_hub.agent.imap.draft_prompt_builder import DraftPromptBuilder
from swiss_ai_hub.agent.imap.extracted_attachment import AttachmentOutcome, ExtractedAttachment
from swiss_ai_hub.agent.imap.parsed_message import ParsedMessage
from swiss_ai_hub.agent.imap.token_budget import MAX_SUBJECT_CHARACTERS, TRUNCATION_MARKER


def _counter(text: str) -> list[int]:
    """One token per four characters — close enough to a real tokenizer to order the trimming decisions."""
    return [0] * (len(text) // 4 + 1)


def _message(body: str = "The delivery never arrived. Please advise.") -> ParsedMessage:
    return ParsedMessage(
        message_id="1",
        sender="alice@test",
        subject="Missing delivery",
        date=datetime(2026, 8, 25, 9, 0, tzinfo=UTC),
        body_text=body,
    )


def _extract(filename: str, text: str, size_bytes: int = 40_000) -> ExtractedAttachment:
    return ExtractedAttachment(
        filename=filename,
        content_type="application/pdf",
        size_bytes=size_bytes,
        outcome=AttachmentOutcome.TEXT,
        text=text,
    )


def _textless(filename: str) -> ExtractedAttachment:
    return ExtractedAttachment(
        filename=filename,
        content_type="image/jpeg",
        size_bytes=84_000,
        outcome=AttachmentOutcome.NO_TEXT,
        detail="no text could be extracted",
    )


def test_a_normal_message_keeps_everything():
    prompt = DraftPromptBuilder(32768, _counter).build(_message(), [_extract("invoice.pdf", "Total 42.00")])

    assert "From: alice@test" in prompt
    assert "Subject: Missing delivery" in prompt
    assert "The delivery never arrived." in prompt
    assert "Total 42.00" in prompt
    assert TRUNCATION_MARKER not in prompt


def test_every_attachment_is_named_including_the_ones_holding_no_text():
    """The sender wrote "see attached" — a reply that never acknowledges the photo is the failure being prevented."""
    prompt = DraftPromptBuilder(32768, _counter).build(_message(), [_textless("cat.jpg")])

    assert "cat.jpg (image/jpeg, 82 KB) — no text could be extracted" in prompt
    assert "Content of the attachment" not in prompt, "a textless attachment must not produce an empty text block"


def test_attachments_are_dropped_before_the_body_is_touched():
    """The body is the message. Reply to a truncated invoice and you still answer the question; drop the question
    and you answer nothing."""
    body = "Please confirm the delivery date. " * 20
    huge = _extract("invoice.pdf", "x" * 20_000)

    prompt = DraftPromptBuilder(400, _counter).build(_message(body), [huge])

    assert "x" * 100 not in prompt, "the oversized attachment should have been dropped"
    assert "Please confirm the delivery date." in prompt
    assert TRUNCATION_MARKER not in prompt, "the body still fits, so it must not be trimmed"


def test_the_smallest_ranked_attachment_is_dropped_first():
    keep = _extract("first.pdf", "A" * 200)
    drop = _extract("second.pdf", "B" * 4_000)

    prompt = DraftPromptBuilder(300, _counter).build(_message("Short body."), [keep, drop])

    assert "A" * 200 in prompt
    assert "B" * 200 not in prompt


def test_the_body_is_trimmed_at_a_sentence_boundary_and_marked():
    """A body cut mid-word invites the model to complete the fragment rather than answer it."""
    body = " ".join(f"Sentence number {index} explains the problem." for index in range(200))

    prompt = DraftPromptBuilder(200, _counter).build(_message(body), [])

    assert TRUNCATION_MARKER in prompt
    assert "Sentence number 0 explains the problem." in prompt
    assert "Sentence number 199 explains the problem." not in prompt


def test_the_envelope_is_never_trimmed_even_when_the_body_goes():
    prompt = DraftPromptBuilder(200, _counter).build(_message("word " * 5_000), [])

    assert "From: alice@test" in prompt
    assert "Subject: Missing delivery" in prompt


def test_a_budget_too_small_for_the_envelope_alone_raises():
    """A misconfiguration, not a runtime condition — emitting a degenerate prompt would spend a model call to reply
    to nothing."""
    builder = DraftPromptBuilder(4, _counter)
    message = _message()

    with pytest.raises(ValueError, match="envelope alone exceeds"):
        builder.build(message, [])


def test_an_enormous_subject_costs_only_its_own_tail():
    """The envelope is the one part `build` never trims, and the subject is attacker-controlled. Without the cap a
    single crafted message would make the envelope unfittable and cost the whole batch its drafts."""
    message = _message()
    message.subject = "A" * 200_000

    prompt = DraftPromptBuilder(32768, _counter).build(message, [])

    assert "A" * MAX_SUBJECT_CHARACTERS in prompt
    assert len(prompt) < 2_000, "the subject was capped, not carried into the prompt whole"


def test_a_short_message_never_pays_for_a_token_count():
    """Counting is a per-message cost on a run already making one model call per message, and almost no mail is
    anywhere near the budget."""
    counter = MagicMock(side_effect=_counter)

    DraftPromptBuilder(32768, counter).build(_message(), [])

    assert counter.call_count == 0
