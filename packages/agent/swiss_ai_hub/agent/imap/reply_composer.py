from email.message import EmailMessage
from email.policy import default as default_policy

from swiss_ai_hub.core.events.agent import MailFetchedEvent

from swiss_ai_hub.agent.imap.parsed_message import ParsedMessage


class ReplyComposer:
    """Wraps an LLM-generated body with a correctly threaded reply envelope for an IMAP draft.

    Only the body text comes from the LLM; recipients, subject, and the In-Reply-To/References threading headers
    are derived deterministically from the original message so the draft threads under it in any mail client.
    """

    @staticmethod
    def compose(fetched: MailFetchedEvent, from_address: str, body: str) -> bytes:
        return ReplyComposer._compose(
            from_address=from_address,
            body=body,
            recipient=ReplyComposer.reply_recipient(fetched),
            subject=fetched.subject,
            rfc_message_id=fetched.rfc_message_id,
            references=fetched.references,
        )

    @staticmethod
    def compose_from_parsed(parsed: ParsedMessage, from_address: str, body: str) -> bytes:
        """Compose a threaded reply from a freshly-fetched ParsedMessage (used by the independent batch drafter)."""
        return ReplyComposer._compose(
            from_address=from_address,
            body=body,
            recipient=parsed.reply_to or parsed.sender,
            subject=parsed.subject,
            rfc_message_id=parsed.rfc_message_id,
            references=parsed.references,
        )

    @staticmethod
    def _compose(
        from_address: str,
        body: str,
        recipient: str,
        subject: str,
        rfc_message_id: str | None,
        references: str | None,
    ) -> bytes:
        message = EmailMessage(policy=default_policy)
        message["From"] = from_address
        message["To"] = recipient
        message["Subject"] = ReplyComposer.reply_subject(subject)

        if rfc_message_id:
            message["In-Reply-To"] = rfc_message_id
            message["References"] = ReplyComposer._references(references, rfc_message_id)

        message.set_content(body)
        return message.as_bytes()

    @staticmethod
    def reply_recipient(fetched: MailFetchedEvent) -> str:
        """The reply is addressed to Reply-To when the sender set one, otherwise back to the From address."""
        return fetched.reply_to or fetched.sender

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
