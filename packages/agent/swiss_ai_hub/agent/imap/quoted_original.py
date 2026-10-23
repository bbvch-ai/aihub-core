import html
from typing import Self

from pydantic import BaseModel
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.imap import DraftEmailSettings, ParsedMessage

from swiss_ai_hub.agent.imap.mail_html_sanitizer import MailHtmlSanitizer

_TEXT_SEPARATOR = "________________________________"


class QuotedOriginal(BaseModel):
    """The original message as Outlook quotes it below a reply: a separator, a From/Sent/To/Cc/Subject block, the body.

    Built after the reply is generated and only ever appended to the draft, so quoting changes neither what the model
    is shown nor what it writes. The labels follow the profile's quote language, the way Outlook's follow the replier's
    language; the run's locale would not do, since a scheduled run carries the platform default, whoever owns the box.
    """

    text: str
    html: str

    @classmethod
    def for_draft(cls, parsed: ParsedMessage, draft: DraftEmailSettings) -> Self | None:
        """The quote for this draft, or None when the admin has quoting switched off."""
        if not draft.quote_original:
            return None
        return cls.from_parsed(parsed, LocaleHandler(draft.quote_locale))

    @classmethod
    def from_parsed(cls, parsed: ParsedMessage, t: LocaleHandler) -> Self:
        header = cls._header_lines(parsed, t)
        body_text = parsed.body_text or MailHtmlSanitizer.to_text(parsed.body_html or "")
        header_text = "\n".join(f"{label}: {value}" for label, value in header)
        header_html = "<br>\n".join(f"<b>{html.escape(label)}:</b> {html.escape(value)}" for label, value in header)
        return cls(
            text=f"{_TEXT_SEPARATOR}\n{header_text}\n\n{body_text}",
            html=(
                '<div id="appendonsend"></div><hr style="display:inline-block;width:98%">'
                f'<div id="divRplyFwdMsg" dir="ltr">{header_html}</div><br>'
                f"<div>{cls._body_html(parsed, body_text)}</div>"
            ),
        )

    @staticmethod
    def _header_lines(parsed: ParsedMessage, t: LocaleHandler) -> list[tuple[str, str]]:
        """Only the headers the original carries: a missing Cc or Date leaves no empty line behind."""
        candidates = [
            ("lib.imap.quote.from", parsed.sender),
            ("lib.imap.quote.sent", parsed.date.strftime(t("lib.imap.quote.date_format")) if parsed.date else None),
            ("lib.imap.quote.to", parsed.to),
            ("lib.imap.quote.cc", parsed.cc),
            ("lib.imap.quote.subject", parsed.subject),
        ]
        return [(t(key), value) for key, value in candidates if value]

    @staticmethod
    def _body_html(parsed: ParsedMessage, body_text: str) -> str:
        if parsed.body_html:
            return MailHtmlSanitizer.original(parsed.body_html)
        return html.escape(body_text).replace("\n", "<br>\n")
