import email
from email.policy import default as default_policy

from swiss_ai_hub.agent.imap.parsed_message import ParsedMessage
from swiss_ai_hub.agent.imap.reply_composer import ReplyComposer


def _parsed(**overrides) -> ParsedMessage:
    base = {
        "message_id": "101",
        "sender": "Alice <alice@example.com>",
        "subject": "Quarterly report",
        "body_text": "Please review the attached numbers.",
        "rfc_message_id": "<orig-123@example.com>",
    }
    base.update(overrides)
    return ParsedMessage(**base)


def _parse(raw: bytes):
    return email.message_from_bytes(raw, policy=default_policy)


def test_compose_from_parsed_sets_threading_headers_and_returns_envelope():
    composed = ReplyComposer.compose_from_parsed(_parsed(), from_address="me@example.com", body="Thanks, looks good.")
    message = _parse(composed.raw)

    assert message["From"] == "me@example.com"
    assert message["To"] == "Alice <alice@example.com>"
    assert message["Subject"] == "Re: Quarterly report"
    assert message["In-Reply-To"] == "<orig-123@example.com>"
    assert message["References"] == "<orig-123@example.com>"
    assert message.get_content().strip() == "Thanks, looks good."

    # The returned envelope mirrors the composed headers, so the persisted ref never drifts from the draft.
    assert composed.subject == "Re: Quarterly report"
    assert composed.recipient == "Alice <alice@example.com>"
    assert composed.in_reply_to == "<orig-123@example.com>"


def test_compose_from_parsed_prefers_reply_to_over_sender():
    composed = ReplyComposer.compose_from_parsed(
        _parsed(reply_to="desk@example.com"), from_address="me@example.com", body="ok"
    )

    assert composed.recipient == "desk@example.com"
    assert _parse(composed.raw)["To"] == "desk@example.com"


def test_reply_subject_is_idempotent():
    assert ReplyComposer.reply_subject("Re: Already replied") == "Re: Already replied"
    assert ReplyComposer.reply_subject("re: lowercase") == "re: lowercase"
    assert ReplyComposer.reply_subject("Fresh topic") == "Re: Fresh topic"


def test_references_chain_appends_original_message_id():
    composed = ReplyComposer.compose_from_parsed(
        _parsed(references="<a@x> <b@x>"), from_address="me@example.com", body="ok"
    )

    assert _parse(composed.raw)["References"] == "<a@x> <b@x> <orig-123@example.com>"
