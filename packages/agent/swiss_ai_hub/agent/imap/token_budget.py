import logging
from collections.abc import Callable

from llama_index.core.node_parser import SentenceSplitter

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

# A subject longer than this is not a subject. Both prompts put it in a fixed part they do not trim — the drafting
# envelope and the classification header — so without a bound here one inbound message could exceed any budget before
# a single trimmable character is considered. The subject is attacker-controlled, which is what makes that reachable.
MAX_SUBJECT_CHARACTERS = 512


class TokenBudget:
    """A token allowance for one prompt, and the measuring and trimming both prompt builders need.

    Extracted so the classification prompt and the drafting prompt bound untrusted mail the same way. They previously
    diverged: drafting measured and trimmed, classification interpolated the body raw, and a message large enough to
    exceed the model's context window failed the whole run rather than being cut down.

    The safety factor is applied here rather than by callers so a budget can only be understood one way — the number
    an admin configures is what the model is sent, not what this class hands to the tokenizer.
    """

    def __init__(self, number_of_input_tokens: int, token_counter: Callable[[str], list[int]]) -> None:
        self._token_counter = token_counter
        self.remaining = int(number_of_input_tokens * BUDGET_SAFETY_FACTOR)

    def reserve(self, text: str) -> None:
        """Take `text` out of the allowance up front, for a fixed part no trimming can reach.

        A system prompt is the case this exists for: admin-editable free text that the model is sent alongside
        everything measured here, so a budget that ignored it would promise a bound it does not hold.
        """
        if text:
            self.remaining -= self.count(text)

    def count(self, text: str) -> int:
        return len(self._token_counter(text))

    def fits(self, text: str) -> bool:
        """Whether `text` is within the allowance, paying for a real count only when the estimate cannot settle it.

        A tokenizer call is a per-message cost on a run that already makes one model call per message, and almost
        every mail is far too short to breach the budget. Under `remaining / 2` characters cannot exceed it for the
        Latin-script content this processes; past `remaining * 4` characters cannot fit, since no tokenizer routed
        through here emits fewer tokens than one per character.
        """
        if len(text) <= self.remaining // SHORT_CIRCUIT_MAX_TOKENS_PER_CHARACTER:
            return True
        if len(text) > self.remaining * 4:
            return False
        return self.count(text) <= self.remaining

    def trim_head(self, text: str, room: int) -> str:
        """Cut `text` to the largest leading run of whole sentences fitting `room` tokens, marked as truncated.

        Sentence boundaries rather than a character slice: text cut mid-word invites the model to complete the
        fragment rather than answer it. The head is kept because a mail states its business first and quotes the
        thread it replies to below.

        `room` is passed in rather than read off `remaining` because the caller knows what else shares the prompt —
        the drafting envelope and the classification instructions are both fixed parts this has to fit around.
        """
        if room <= 0:
            return TRUNCATION_MARKER

        splitter = SentenceSplitter(
            chunk_size=max(1, room),
            chunk_overlap=0,
            tokenizer=lambda chunk: [0] * self.count(chunk),
        )
        head = next(iter(splitter.split_text(text)), "")
        logger.info("[token-budget] trimmed text from %d to %d characters", len(text), len(head))
        return f"{head}\n\n{TRUNCATION_MARKER}"
