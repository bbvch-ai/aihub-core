from email.message import EmailMessage
from email.policy import default as default_policy

from swiss_ai_hub.core.imap import ParsedMessage

from swiss_ai_hub.agent.imap.composed_reply import ComposedReply
from swiss_ai_hub.agent.imap.draft_body_renderer import DraftBodyRenderer
from swiss_ai_hub.agent.imap.mail_html_sanitizer import OUTLOOK_FONT_STYLE
from swiss_ai_hub.agent.imap.quoted_original import QuotedOriginal


class ReplyComposer:
    """Wraps an LLM-generated body with a correctly threaded reply envelope for an IMAP draft.

    Only the body text comes from the LLM; recipient, subject, and the In-Reply-To/References threading headers
    are derived deterministically from the original message so the draft threads under it in any mail client.
    The body becomes a sanitised HTML part with a plain-text alternative, so formatting renders where HTML does and
    the draft stays readable where it does not.
    """

    @staticmethod
    def compose_from_parsed(
        parsed: ParsedMessage, from_address: str, body: str, quoted: QuotedOriginal | None = None
    ) -> ComposedReply:
        """Compose a threaded reply from a freshly-fetched ParsedMessage, returning the raw bytes and its envelope."""
        recipient = parsed.reply_to or parsed.sender
        subject = ReplyComposer.reply_subject(parsed.subject)

        message = EmailMessage(policy=default_policy)
        message["From"] = from_address
        message["To"] = recipient
        message["Subject"] = subject
        if parsed.rfc_message_id:
            message["In-Reply-To"] = parsed.rfc_message_id
            message["References"] = ReplyComposer._references(parsed.references, parsed.rfc_message_id)

        message.set_content(ReplyComposer._text_part(body, quoted))
        message.add_alternative(ReplyComposer._html_part(body, quoted), subtype="html")
        return ComposedReply(
            raw=message.as_bytes(), subject=subject, recipient=recipient, in_reply_to=parsed.rfc_message_id
        )

    @staticmethod
    def reply_subject(subject: str) -> str:
        """Prefix ``Re:`` unless the subject already carries one, so replies don't accumulate ``Re: Re:``."""
        stripped = subject.strip()
        if stripped.lower().startswith("re:"):
            return stripped
        return f"Re: {stripped}"

    @staticmethod
    def _text_part(body: str, quoted: QuotedOriginal | None) -> str:
        reply = DraftBodyRenderer.text(body)
        return f"{reply}\n\n{quoted.text}\n" if quoted else f"{reply}\n"

    @staticmethod
    def _html_part(body: str, quoted: QuotedOriginal | None) -> str:
        reply = f'<div style="{OUTLOOK_FONT_STYLE}">{DraftBodyRenderer.html(body)}</div>'
        # Word does not carry a div's font into table cells, so without this rule every table, the model's or the
        # quoted original's, renders in Times New Roman. A cell's own inline style still wins over it.
        head = f'<meta charset="utf-8"><style>td,th{{{OUTLOOK_FONT_STYLE}}}</style>'
        return f"<html><head>{head}</head><body>{reply}{quoted.html if quoted else ''}</body></html>"

    @staticmethod
    def _references(original_references: str | None, rfc_message_id: str) -> str:
        """Append the original Message-ID to any existing References chain, per RFC 5322 threading."""
        if original_references:
            return f"{original_references.strip()} {rfc_message_id}"
        return rfc_message_id
