import email
from email.message import EmailMessage
from email.policy import default as default_policy
from unittest.mock import Mock, patch

import pytest

from swiss_ai_hub.agent.imap.mail_parser import MailParser
from swiss_ai_hub.agent.imap.mail_store import MailStore
from swiss_ai_hub.agent.imap.parsed_message import ParsedAttachment

_STORE_MODULE = "swiss_ai_hub.agent.imap.mail_store"
_AGENT_CLASS = "ImapAgent"
_AGENT_ID = "imap-agent"


def _raw_message() -> bytes:
    """A multipart mail exercising every field the issue's acceptance criteria list, plus an attachment."""
    message = EmailMessage()
    message["Subject"] = "Quarterly report"
    message["From"] = "sender@example.com"
    message["To"] = "primary@example.com, second@example.com"
    message["Cc"] = "watcher@example.com"
    message["Date"] = "Wed, 12 Aug 2026 09:30:00 +0200"
    message["Message-ID"] = "<report-1@example.com>"
    message.set_content("Please find the report attached.")
    message.add_alternative("<p>Please find the report <b>attached</b>.</p>", subtype="html")
    message.add_attachment(
        b"%PDF-1.4 fake",
        maintype="application",
        subtype="pdf",
        filename="report.pdf",
    )
    return message.as_bytes()


class TestStoreMessage:
    @pytest.mark.asyncio
    async def test_writes_the_raw_bytes_verbatim(self):
        raw = _raw_message()
        client = Mock()

        with patch(f"{_STORE_MODULE}.create_s3_client", return_value=client):
            ref = await MailStore.store_message(raw, message_id="42", agent_class=_AGENT_CLASS, agent_id=_AGENT_ID)

        assert ref is not None
        assert ref.size_bytes == len(raw)
        assert client.put_object.call_args.kwargs["Body"] == raw

    @pytest.mark.asyncio
    async def test_stores_as_a_non_rendering_download(self):
        """The archived mail keeps its attacker-controlled HTML, so the object must not render inline in a
        browser. Sanitizing is a render-time obligation; this header is the transport-level guard."""
        client = Mock()

        with patch(f"{_STORE_MODULE}.create_s3_client", return_value=client):
            await MailStore.store_message(b"raw", message_id="42", agent_class=_AGENT_CLASS, agent_id=_AGENT_ID)

        kwargs = client.put_object.call_args.kwargs
        assert kwargs["ContentType"] == "message/rfc822"
        assert kwargs["ContentDisposition"] == "attachment"

    @pytest.mark.asyncio
    async def test_writes_to_the_location_the_reference_resolves_to(self):
        client = Mock()

        with patch(f"{_STORE_MODULE}.create_s3_client", return_value=client):
            ref = await MailStore.store_message(b"raw", message_id="42", agent_class=_AGENT_CLASS, agent_id=_AGENT_ID)

        bucket, key = ref.resolve_s3_location(_AGENT_CLASS, _AGENT_ID)
        kwargs = client.put_object.call_args.kwargs
        assert (kwargs["Bucket"], kwargs["Key"]) == (bucket, key)
        assert key.endswith("42.eml")

    @pytest.mark.asyncio
    async def test_stores_nothing_when_there_are_no_raw_bytes(self):
        """A message parsed from an in-memory fixture carries no raw bytes; that must not put an empty
        object nor fail the run."""
        client = Mock()

        with patch(f"{_STORE_MODULE}.create_s3_client", return_value=client):
            ref = await MailStore.store_message(b"", message_id="42", agent_class=_AGENT_CLASS, agent_id=_AGENT_ID)

        assert ref is None
        client.put_object.assert_not_called()


class TestArchivedOriginalRoundTrips:
    """The acceptance criterion is that the stored mail "can be retrieved for future processing", so the
    test that matters reads the archived bytes back and checks every field the issue enumerates — including
    the recipients, which exist nowhere else: MailParser never extracted To/Cc onto ParsedMessage."""

    @pytest.mark.asyncio
    async def test_every_field_survives_the_round_trip(self):
        raw = _raw_message()
        client = Mock()

        with patch(f"{_STORE_MODULE}.create_s3_client", return_value=client):
            await MailStore.store_message(raw, message_id="42", agent_class=_AGENT_CLASS, agent_id=_AGENT_ID)

        restored = email.message_from_bytes(client.put_object.call_args.kwargs["Body"], policy=default_policy)

        assert restored["Subject"] == "Quarterly report"
        assert restored["From"] == "sender@example.com"
        assert restored["To"] == "primary@example.com, second@example.com"
        assert restored["Cc"] == "watcher@example.com"
        assert restored["Date"] == "Wed, 12 Aug 2026 09:30:00 +0200"
        assert "Please find the report attached." in restored.get_body(("plain",)).get_content()
        assert [part.get_filename() for part in restored.iter_attachments()] == ["report.pdf"]

    @pytest.mark.asyncio
    async def test_preserves_content_the_event_deliberately_omits(self):
        """body_html and the recipients are kept off MailFetchedEvent on purpose (XSS / payload size).
        Archiving the original is what stops that being data loss."""
        raw = _raw_message()
        parsed = MailParser.parse_message("42", email.message_from_bytes(raw, policy=default_policy), 1024, 1024, raw)
        client = Mock()

        with patch(f"{_STORE_MODULE}.create_s3_client", return_value=client):
            await MailStore.store_message(
                parsed.raw, message_id=parsed.message_id, agent_class=_AGENT_CLASS, agent_id=_AGENT_ID
            )

        restored = email.message_from_bytes(client.put_object.call_args.kwargs["Body"], policy=default_policy)
        assert restored["To"] == "primary@example.com, second@example.com"
        assert "<b>attached</b>" in restored.get_body(("html",)).get_content()

    @pytest.mark.asyncio
    async def test_body_truncation_never_reaches_the_archive(self):
        """max_body_bytes trims what the event may carry. The archive must ignore that bound entirely,
        otherwise the "original" would silently be a truncated copy."""
        raw = _raw_message()
        parsed = MailParser.parse_message("42", email.message_from_bytes(raw, policy=default_policy), 5, 1024, raw)
        client = Mock()

        with patch(f"{_STORE_MODULE}.create_s3_client", return_value=client):
            await MailStore.store_message(
                parsed.raw, message_id=parsed.message_id, agent_class=_AGENT_CLASS, agent_id=_AGENT_ID
            )

        assert len(parsed.body_text or "") <= 5
        assert client.put_object.call_args.kwargs["Body"] == raw


class TestAttachmentsAreStoredAlongsideTheOriginal:
    @pytest.mark.asyncio
    async def test_both_are_stored_for_a_message_with_an_attachment(self):
        """Acceptance criterion: existing attachment storage keeps working. The attachment therefore exists
        twice — inline in the archived .eml and as its own object — which is accepted deliberately."""
        raw = _raw_message()
        parsed = MailParser.parse_message("42", email.message_from_bytes(raw, policy=default_policy), 1024, 1024, raw)
        client = Mock()

        with patch(f"{_STORE_MODULE}.create_s3_client", return_value=client):
            attachment_refs = await MailStore.store_attachments(parsed.attachments, _AGENT_CLASS, _AGENT_ID)
            message_ref = await MailStore.store_message(
                parsed.raw, message_id=parsed.message_id, agent_class=_AGENT_CLASS, agent_id=_AGENT_ID
            )

        assert [ref.filename for ref in attachment_refs] == ["report.pdf"]
        assert message_ref is not None
        assert client.put_object.call_count == 2


class TestLoadingBackFromTheArchive:
    """Reading an archived message back is what lets a step run after the mail has been filed.

    The IMAP UID dies with the MOVE that files a message, so a drafting pass cannot re-fetch it. The archive is keyed
    by file_id and does not move, which makes it the only durable handle on the content.
    """

    @pytest.mark.asyncio
    async def test_a_stored_message_comes_back_byte_identical(self):
        raw = _raw_message()
        client = Mock()

        with patch(f"{_STORE_MODULE}.create_s3_client", return_value=client):
            ref = await MailStore.store_message(raw, message_id="42", agent_class=_AGENT_CLASS, agent_id=_AGENT_ID)
            client.get_object.return_value = {"Body": Mock(read=Mock(return_value=raw))}
            loaded = await MailStore.load_message(ref, agent_class=_AGENT_CLASS, agent_id=_AGENT_ID)

        assert loaded == raw

    @pytest.mark.asyncio
    async def test_a_message_is_read_from_the_location_its_reference_resolves_to(self):
        raw = _raw_message()
        client = Mock()

        with patch(f"{_STORE_MODULE}.create_s3_client", return_value=client):
            ref = await MailStore.store_message(raw, message_id="42", agent_class=_AGENT_CLASS, agent_id=_AGENT_ID)
            client.get_object.return_value = {"Body": Mock(read=Mock(return_value=raw))}
            await MailStore.load_message(ref, agent_class=_AGENT_CLASS, agent_id=_AGENT_ID)

        written = client.put_object.call_args.kwargs
        read = client.get_object.call_args.kwargs
        assert (read["Bucket"], read["Key"]) == (written["Bucket"], written["Key"])

    @pytest.mark.asyncio
    async def test_the_reparsed_message_still_carries_the_threading_headers(self):
        """The reply's In-Reply-To and References come out of these bytes, so the round trip has to preserve them."""
        raw = _raw_message()
        client = Mock()

        with patch(f"{_STORE_MODULE}.create_s3_client", return_value=client):
            ref = await MailStore.store_message(raw, message_id="42", agent_class=_AGENT_CLASS, agent_id=_AGENT_ID)
            client.get_object.return_value = {"Body": Mock(read=Mock(return_value=raw))}
            loaded = await MailStore.load_message(ref, agent_class=_AGENT_CLASS, agent_id=_AGENT_ID)

        parsed = MailParser.parse_message(
            "42", email.message_from_bytes(loaded, policy=default_policy), 1_000_000, 10_000_000, raw=b""
        )
        assert parsed.rfc_message_id == "<report-1@example.com>"
        assert parsed.sender == "sender@example.com"
        assert parsed.subject == "Quarterly report"
        assert "report attached" in parsed.body_text

    @pytest.mark.asyncio
    async def test_a_stored_attachment_comes_back_byte_identical(self):
        content = b"%PDF-1.4 fake"
        client = Mock()

        with patch(f"{_STORE_MODULE}.create_s3_client", return_value=client):
            refs = await MailStore.store_attachments(
                [ParsedAttachment(filename="report.pdf", content_type="application/pdf", content=content)],
                agent_class=_AGENT_CLASS,
                agent_id=_AGENT_ID,
            )
            client.get_object.return_value = {"Body": Mock(read=Mock(return_value=content))}
            loaded = await MailStore.load_attachment(refs[0], agent_class=_AGENT_CLASS, agent_id=_AGENT_ID)

        assert loaded == content
