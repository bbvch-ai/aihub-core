from datetime import datetime
from email.message import EmailMessage
from email.utils import parsedate_to_datetime

from swiss_ai_hub.core.events.agent import UnreadMailSummary

from swiss_ai_hub.agent.imap.parsed_message import ParsedAttachment, ParsedMessage


class MailParser:
    """Turns raw RFC822 bytes into domain objects — header summaries and fully parsed messages."""

    @staticmethod
    def parse_summary(message_id: str, message: EmailMessage, flags: list[str]) -> UnreadMailSummary:
        return UnreadMailSummary(
            message_id=message_id,
            sender=message.get("From", ""),
            subject=message.get("Subject", ""),
            date=MailParser._parse_date(message.get("Date")),
            flags=flags,
        )

    @staticmethod
    def parse_message(
        message_id: str,
        message: EmailMessage,
        max_body_bytes: int,
        max_attachment_bytes: int,
    ) -> ParsedMessage:
        """Parse a MIME message, truncating bodies and dropping oversized attachments so a hostile or
        oversized mail can never bloat the persisted/streamed event or the agent's memory footprint."""
        body_text: str | None = None
        body_html: str | None = None
        attachments: list[ParsedAttachment] = []

        for part in message.walk():
            if part.is_multipart():
                continue
            content_type = part.get_content_type()
            filename = part.get_filename()
            disposition = part.get_content_disposition()

            if disposition == "attachment" or filename:
                payload = part.get_payload(decode=True) or b""
                if len(payload) > max_attachment_bytes:
                    continue
                attachments.append(
                    ParsedAttachment(
                        filename=MailParser._safe_filename(filename or "attachment"),
                        content_type=content_type,
                        content=payload,
                    )
                )
            elif content_type == "text/plain" and body_text is None:
                body_text = MailParser._decode_text(part, max_body_bytes)
            elif content_type == "text/html" and body_html is None:
                body_html = MailParser._decode_text(part, max_body_bytes)

        return ParsedMessage(
            message_id=message_id,
            sender=message.get("From", ""),
            subject=message.get("Subject", ""),
            date=MailParser._parse_date(message.get("Date")),
            body_text=body_text,
            body_html=body_html,
            attachments=attachments,
        )

    @staticmethod
    def _decode_text(part: EmailMessage, max_bytes: int) -> str:
        payload = part.get_payload(decode=True) or b""
        charset = part.get_content_charset() or "utf-8"
        text = payload.decode(charset, errors="replace")
        encoded = text.encode("utf-8")
        if len(encoded) <= max_bytes:
            return text
        return encoded[:max_bytes].decode("utf-8", errors="ignore")

    @staticmethod
    def _parse_date(raw_date: str | None) -> datetime | None:
        if not raw_date:
            return None
        try:
            return parsedate_to_datetime(raw_date)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _safe_filename(filename: str) -> str:
        return filename.replace("/", "_").replace("\\", "_").replace("..", "_")
