import email
from email.policy import default as default_policy

from swiss_ai_hub.core.events.agent import MailFetchedEvent

from swiss_ai_hub.agent.imap.reply_composer import ReplyComposer


def _fetched(**overrides) -> MailFetchedEvent:
    base = {
        "message_id": "101",
        "sender": "Alice <alice@example.com>",
        "subject": "Quarterly report",
        "body_text": "Please review the attached numbers.",
        "rfc_message_id": "<orig-123@example.com>",
    }
    base.update(overrides)
    return MailFetchedEvent(**base)


def _parse(raw: bytes):
    return email.message_from_bytes(raw, policy=default_policy)


def test_compose_sets_threading_headers_and_llm_body():
    raw = ReplyComposer.compose(_fetched(), from_address="me@example.com", body="Thanks, looks good.")
    message = _parse(raw)

    assert message["From"] == "me@example.com"
    assert message["To"] == "Alice <alice@example.com>"
    assert message["Subject"] == "Re: Quarterly report"
    assert message["In-Reply-To"] == "<orig-123@example.com>"
    assert message["References"] == "<orig-123@example.com>"
    assert message.get_content().strip() == "Thanks, looks good."


def test_reply_subject_is_idempotent():
    assert ReplyComposer.reply_subject("Re: Already replied") == "Re: Already replied"
    assert ReplyComposer.reply_subject("re: lowercase") == "re: lowercase"
    assert ReplyComposer.reply_subject("Fresh topic") == "Re: Fresh topic"


def test_references_chain_appends_original_message_id():
    fetched = _fetched(references="<a@x> <b@x>")
    raw = ReplyComposer.compose(fetched, from_address="me@example.com", body="ok")
    message = _parse(raw)

    assert message["References"] == "<a@x> <b@x> <orig-123@example.com>"


def test_recipient_prefers_reply_to_over_sender():
    fetched = _fetched(reply_to="desk@example.com")
    assert ReplyComposer.reply_recipient(fetched) == "desk@example.com"
    assert ReplyComposer.reply_recipient(_fetched()) == "Alice <alice@example.com>"
