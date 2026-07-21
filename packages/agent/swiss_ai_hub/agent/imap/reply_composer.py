from email.message import EmailMessage
from email.policy import default as default_policy

from swiss_ai_hub.agent.imap.composed_reply import ComposedReply
from swiss_ai_hub.agent.imap.parsed_message import ParsedMessage


class ReplyComposer:
    """Wraps an LLM-generated body with a correctly threaded reply envelope for an IMAP draft.

    Only the body text comes from the LLM; recipient, subject, and the In-Reply-To/References threading headers
    are derived deterministically from the original message so the draft threads under it in any mail client.
    """

    @staticmethod
    def compose_from_parsed(parsed: ParsedMessage, from_address: str, body: str) -> ComposedReply:
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

        message.set_content(body)
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
    def _references(original_references: str | None, rfc_message_id: str) -> str:
        """Append the original Message-ID to any existing References chain, per RFC 5322 threading."""
        if original_references:
            return f"{original_references.strip()} {rfc_message_id}"
        return rfc_message_id
