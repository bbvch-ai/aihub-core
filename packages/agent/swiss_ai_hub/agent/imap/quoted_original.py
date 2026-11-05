import html
from datetime import UTC, datetime
from typing import Self
from zoneinfo import ZoneInfo

from pydantic import BaseModel
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.imap import DraftEmailSettings, ParsedMessage

from swiss_ai_hub.agent.imap.mail_html_sanitizer import OUTLOOK_FONT_STYLE, MailHtmlSanitizer

_TEXT_SEPARATOR = "________________________________"


class QuotedOriginal(BaseModel):
    """The original message as Outlook quotes it below a reply: a separator, a From/Sent/To/Cc/Subject block, the body.

    Built after the reply is generated and only ever appended to the draft, so quoting changes neither what the model
    is shown nor what it writes. The labels follow the profile's quote language and the Sent date its quote timezone,
    the way Outlook's follow the replier; the run's locale would not do, since a scheduled run carries the platform
    default, whoever owns the box.
    """

    text: str
    html: str

    @classmethod
    def for_draft(cls, parsed: ParsedMessage, draft: DraftEmailSettings) -> Self | None:
        """The quote for this draft, or None when the admin has quoting switched off."""
        if not draft.quote_original:
            return None
        return cls.from_parsed(parsed, LocaleHandler(draft.quote_locale), ZoneInfo(draft.quote_timezone))

    @classmethod
    def from_parsed(cls, parsed: ParsedMessage, t: LocaleHandler, zone: ZoneInfo) -> Self:
        header = cls._header_lines(parsed, t, zone)
        body_text = parsed.body_text or MailHtmlSanitizer.to_text(parsed.body_html or "")
        header_text = "\n".join(f"{label}: {value}" for label, value in header)
        header_html = "<br>\n".join(f"<b>{html.escape(label)}:</b> {html.escape(value)}" for label, value in header)
        # The font is set on both blocks because the sanitiser drops the original's <style> sheet, and Outlook's Word
        # engine falls back to Times New Roman for any text that no longer names a font.
        return cls(
            text=f"{_TEXT_SEPARATOR}\n{header_text}\n\n{body_text}",
            html=(
                '<div id="appendonsend"></div><hr style="display:inline-block;width:98%">'
                f'<div id="divRplyFwdMsg" dir="ltr" style="{OUTLOOK_FONT_STYLE}">{header_html}</div><br>'
                f'<div style="{OUTLOOK_FONT_STYLE}">{cls._body_html(parsed, body_text)}</div>'
            ),
        )

    @staticmethod
    def _header_lines(parsed: ParsedMessage, t: LocaleHandler, zone: ZoneInfo) -> list[tuple[str, str]]:
        """Only the headers the original carries: a missing Cc or Date leaves no empty line behind."""
        candidates = [
            ("lib.imap.quote.from", parsed.sender),
            ("lib.imap.quote.sent", QuotedOriginal._sent(parsed.date, t, zone) if parsed.date else None),
            ("lib.imap.quote.to", parsed.to),
            ("lib.imap.quote.cc", parsed.cc),
            ("lib.imap.quote.subject", parsed.subject),
        ]
        return [(t(key), value) for key, value in candidates if value]

    @staticmethod
    def _sent(date: datetime, t: LocaleHandler, zone: ZoneInfo) -> str:
        """The Date header in the replier's zone. A `-0000` header parses without a zone; RFC 5322 makes it UTC."""
        aware = date if date.tzinfo else date.replace(tzinfo=UTC)
        return aware.astimezone(zone).strftime(t("lib.imap.quote.date_format"))

    @staticmethod
    def _body_html(parsed: ParsedMessage, body_text: str) -> str:
        if parsed.body_html:
            return MailHtmlSanitizer.original(parsed.body_html)
        return html.escape(body_text).replace("\n", "<br>\n")
