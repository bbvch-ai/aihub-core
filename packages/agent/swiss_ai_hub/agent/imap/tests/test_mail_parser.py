import email
from email.message import EmailMessage
from email.policy import default as default_policy

from swiss_ai_hub.agent.imap.mail_parser import MailParser

_MAX_BODY_BYTES = 1_000_000
_MAX_ATTACHMENT_BYTES = 10_000_000


def _parse(
    message: EmailMessage, max_body_bytes: int = _MAX_BODY_BYTES, max_attachment_bytes: int = _MAX_ATTACHMENT_BYTES
):
    return MailParser.parse_message("42", message, max_body_bytes, max_attachment_bytes)


def _from_bytes(message: EmailMessage) -> EmailMessage:
    return email.message_from_bytes(message.as_bytes(), policy=default_policy)


def _build_message() -> EmailMessage:
    message = EmailMessage()
    message["From"] = "Alice <alice@example.com>"
    message["Subject"] = "Quarterly report"
    message["Date"] = "Mon, 05 Jan 2026 10:00:00 +0000"
    message.set_content("Please find the report attached.")
    message.add_alternative("<p>Please find the report attached.</p>", subtype="html")
    message.add_attachment(b"%PDF-1.4 fake", maintype="application", subtype="pdf", filename="report.pdf")
    return _from_bytes(message)


def test_parse_summary_extracts_headers():
    summary = MailParser.parse_summary("42", _build_message(), flags=["\\Seen"])

    assert summary.message_id == "42"
    assert summary.sender == "Alice <alice@example.com>"
    assert summary.subject == "Quarterly report"
    assert summary.date is not None
    assert summary.flags == ["\\Seen"]


def test_parse_message_extracts_bodies_and_attachments():
    parsed = _parse(_build_message())

    assert parsed.body_text is not None
    assert "report attached" in parsed.body_text
    assert parsed.body_html is not None
    assert "<p>" in parsed.body_html
    assert len(parsed.attachments) == 1
    attachment = parsed.attachments[0]
    assert attachment.filename == "report.pdf"
    assert attachment.content_type == "application/pdf"
    assert attachment.content.startswith(b"%PDF")


def test_parse_message_sanitizes_attachment_filename():
    message = EmailMessage()
    message["From"] = "a@example.com"
    message["Subject"] = "evil"
    message.set_content("body")
    message.add_attachment(b"x", maintype="application", subtype="octet-stream", filename="../../etc/passwd")
    parsed = _parse(_from_bytes(message))

    assert "/" not in parsed.attachments[0].filename
    assert ".." not in parsed.attachments[0].filename


def test_parse_message_truncates_oversized_body():
    message = EmailMessage()
    message["From"] = "a@example.com"
    message["Subject"] = "big"
    message.set_content("x" * 5000)
    parsed = _parse(_from_bytes(message), max_body_bytes=100)

    assert parsed.body_text is not None
    assert len(parsed.body_text.encode("utf-8")) <= 100


def test_parse_message_skips_oversized_attachment():
    message = EmailMessage()
    message["From"] = "a@example.com"
    message["Subject"] = "big attachment"
    message.set_content("body")
    message.add_attachment(b"y" * 5000, maintype="application", subtype="octet-stream", filename="huge.bin")
    parsed = _parse(_from_bytes(message), max_attachment_bytes=100)

    assert parsed.attachments == []


def test_parse_date_handles_missing_date():
    message = EmailMessage()
    message["From"] = "a@example.com"
    message["Subject"] = "no date"
    message.set_content("body")
    summary = MailParser.parse_summary("1", _from_bytes(message), [])

    assert summary.date is None
