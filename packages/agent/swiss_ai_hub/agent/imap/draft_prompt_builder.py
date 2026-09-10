import logging
from collections.abc import Callable

from swiss_ai_hub.agent.imap.extracted_attachment import AttachmentOutcome, ExtractedAttachment
from swiss_ai_hub.agent.imap.parsed_message import ParsedMessage
from swiss_ai_hub.agent.imap.token_budget import MAX_SUBJECT_CHARACTERS, TRUNCATION_MARKER, TokenBudget

logger = logging.getLogger(__name__)


class DraftPromptBuilder:
    """Renders the drafting prompt, guaranteed to fit the configured input-token budget.

    The budget covers what the model is actually sent, so the system prompt is subtracted from it up front rather than
    ignored: `draft_prompt` is admin-editable free text, and a pasted style guide would otherwise overflow a budget
    the admin was told bounds the whole prompt.

    The parts are not equal, so trimming is ordered rather than proportional. The envelope (who wrote, about what,
    what they attached) is never trimmed — it is a few dozen tokens and the reply is meaningless without it. The body
    is trimmed only after every attachment has been given up, because the body *is* the message: reply to a truncated
    invoice and you still answer the sender's question, drop the question and you answer nothing.

    Measuring costs a tokenizer call, so most mail never pays for one — a message comfortably under budget is
    accepted on its character count alone, the same short-circuit core's chunk limiter uses.
    """

    def __init__(
        self,
        number_of_input_tokens: int,
        token_counter: Callable[[str], list[int]],
        system_prompt: str = "",
    ) -> None:
        self._budget = TokenBudget(number_of_input_tokens, token_counter)
        self._budget.reserve(system_prompt)
        if self._budget.remaining <= 0:
            raise ValueError(
                f"the drafting system prompt alone exhausts the {number_of_input_tokens}-token budget — shorten "
                f"draft_prompt or raise number_of_input_tokens on the draft settings"
            )

    def build(self, parsed: ParsedMessage, attachments: list[ExtractedAttachment]) -> str:
        """Render the user half of the prompt for one message, dropping and trimming until it fits."""
        envelope = self._envelope(parsed, attachments)
        body = (parsed.body_text or "").strip()

        self._reject_unfittable_envelope(envelope)

        extracts = [attachment for attachment in attachments if attachment.outcome is AttachmentOutcome.TEXT]
        while extracts:
            candidate = self._render(envelope, body, extracts)
            if self._budget.fits(candidate):
                return candidate
            dropped = extracts.pop()
            logger.info(
                "[draft-prompt] dropped the extracted text of %r to fit the %d-token budget",
                dropped.filename,
                self._budget.remaining,
            )

        candidate = self._render(envelope, body, [])
        if self._budget.fits(candidate):
            return candidate

        return self._render(envelope, self._trim_body(envelope, body), [])

    def _reject_unfittable_envelope(self, envelope: str) -> None:
        """Fail loudly when the parts that must never be trimmed already exceed the budget.

        Reachable only by misconfiguration now that the subject is capped: a budget too small for a bounded envelope
        is an admin error, and emitting a degenerate prompt would spend a model call to produce a reply to nothing.
        Mirrors what `limit_chat_history_with_context` does when the system and user messages alone overflow.
        """
        if self._budget.fits(self._render(envelope, "", [])):
            return
        raise ValueError(
            f"the message envelope alone exceeds the {self._budget.remaining}-token drafting budget — raise "
            f"number_of_input_tokens on the draft settings"
        )

    def _trim_body(self, envelope: str, body: str) -> str:
        """Cut the body down to whatever the envelope and the truncation marker leave room for."""
        room = self._budget.remaining - self._budget.count(self._render(envelope, TRUNCATION_MARKER, []))
        return self._budget.trim_head(body, room)

    @staticmethod
    def _envelope(parsed: ParsedMessage, attachments: list[ExtractedAttachment]) -> str:
        """The headers plus one inventory line per attachment considered, whatever reading it produced.

        Every attachment is named, including the ones that yielded nothing: the model needs to know a photo arrived
        so it can acknowledge it, and needs to be told there is no text so it does not invent any.
        """
        lines = [f"From: {parsed.sender}", f"Subject: {parsed.subject[:MAX_SUBJECT_CHARACTERS]}"]
        if parsed.date:
            lines.append(f"Date: {parsed.date.isoformat()}")
        if attachments:
            lines.append("Attachments:")
            lines.extend(f"  - {attachment.inventory_line}" for attachment in attachments)
        return "\n".join(lines)

    @staticmethod
    def _render(envelope: str, body: str, extracts: list[ExtractedAttachment]) -> str:
        sections = [envelope, "", body]
        for extract in extracts:
            sections.extend(["", f"--- Content of the attachment {extract.filename} ---", extract.text])
        return "\n".join(sections)
