import logging
from collections.abc import Callable

from llama_index.core.node_parser import SentenceSplitter

from swiss_ai_hub.agent.imap.extracted_attachment import AttachmentOutcome, ExtractedAttachment
from swiss_ai_hub.agent.imap.parsed_message import ParsedMessage

logger = logging.getLogger(__name__)

# Absorbs what the count cannot know: `get_tokenizer()` is not the tokenizer of whichever model LiteLLM routes to,
# and the chat envelope around the rendered text costs tokens of its own. Same value and same reasoning as
# SUMMARIZATION_BUDGET_SAFETY_FACTOR in core's recursive_summary_parser.
BUDGET_SAFETY_FACTOR = 0.85

# Worst-case tokens per character for the accept short-circuit — see the identical constant in core's
# TextChunkSizeLimiter and recursive_summary_parser. Deployments process Latin-script EU-language content, where even
# a multi-byte accented character costs at most ~2 tokens under byte-level BPE fallback. Raise toward 3 for CJK.
SHORT_CIRCUIT_MAX_TOKENS_PER_CHARACTER = 2

TRUNCATION_MARKER = "[… truncated]"


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
        self._token_counter = token_counter
        self._budget = int(number_of_input_tokens * BUDGET_SAFETY_FACTOR) - self._count_or_zero(system_prompt)
        if self._budget <= 0:
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
            if self._fits(candidate):
                return candidate
            dropped = extracts.pop()
            logger.info(
                "[draft-prompt] dropped the extracted text of %r to fit the %d-token budget",
                dropped.filename,
                self._budget,
            )

        candidate = self._render(envelope, body, [])
        if self._fits(candidate):
            return candidate

        return self._render(envelope, self._trim_body(envelope, body), [])

    def _reject_unfittable_envelope(self, envelope: str) -> None:
        """Fail loudly when the parts that must never be trimmed already exceed the budget.

        A budget too small for the headers alone is a misconfiguration, and emitting a degenerate prompt would spend
        a model call to produce a reply to nothing. Mirrors what `limit_chat_history_with_context` does when the
        system and user messages alone overflow.
        """
        if self._fits(self._render(envelope, "", [])):
            return
        raise ValueError(
            f"the message envelope alone exceeds the {self._budget}-token drafting budget — raise "
            f"number_of_input_tokens on the draft settings"
        )

    def _trim_body(self, envelope: str, body: str) -> str:
        """Cut the body to the largest leading run of whole sentences that fits, marked as truncated.

        Sentence boundaries rather than a character slice: a body cut mid-word invites the model to complete the
        fragment rather than answer it. The head is kept because a mail states its business first and quotes the
        thread it replies to below.
        """
        room = self._budget - self._count(self._render(envelope, TRUNCATION_MARKER, []))
        if room <= 0:
            return TRUNCATION_MARKER

        splitter = SentenceSplitter(
            chunk_size=max(1, room),
            chunk_overlap=0,
            tokenizer=lambda text: [0] * self._count(text),
        )
        head = next(iter(splitter.split_text(body)), "")
        logger.info("[draft-prompt] trimmed the body from %d to %d characters", len(body), len(head))
        return f"{head}\n\n{TRUNCATION_MARKER}"

    @staticmethod
    def _envelope(parsed: ParsedMessage, attachments: list[ExtractedAttachment]) -> str:
        """The headers plus one inventory line per attachment considered, whatever reading it produced.

        Every attachment is named, including the ones that yielded nothing: the model needs to know a photo arrived
        so it can acknowledge it, and needs to be told there is no text so it does not invent any.
        """
        lines = [f"From: {parsed.sender}", f"Subject: {parsed.subject}"]
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

    def _fits(self, text: str) -> bool:
        """Whether `text` is within budget, paying for a real count only when the estimate cannot settle it.

        A tokenizer call is a per-message cost on a run that already makes one model call per message, and almost
        every mail is far too short to breach the budget. Under `budget / 2` characters cannot exceed it for the
        Latin-script content this processes; past `budget * 4` characters cannot fit, since no tokenizer routed
        through here emits fewer tokens than one per character.
        """
        if len(text) <= self._budget // SHORT_CIRCUIT_MAX_TOKENS_PER_CHARACTER:
            return True
        if len(text) > self._budget * 4:
            return False
        return self._count(text) <= self._budget

    def _count(self, text: str) -> int:
        return len(self._token_counter(text))

    def _count_or_zero(self, text: str) -> int:
        """An empty system prompt costs nothing and must not cost a tokenizer call either — construction happens once
        per batch, and the short-circuit in `_fits` is there precisely to keep a short message from paying for one."""
        return self._count(text) if text else 0
