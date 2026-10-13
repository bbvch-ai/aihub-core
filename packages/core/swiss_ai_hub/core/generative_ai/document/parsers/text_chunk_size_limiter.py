from collections.abc import Callable

from llama_index.core.node_parser import SentenceSplitter

from swiss_ai_hub.core.generative_ai.document.parsers.text_chunk import TextChunk

# Worst-case tokens per character assumed by `_within_budget`'s accept short-circuit -- see the identical
# constant and rationale in recursive_summary_parser.py. Kept separate since the two budgets are independent
# decisions that happen to share this assumption: deployments process Latin-script EU-language content, not
# CJK, so a character costs at most ~2 tokens even under byte-level BPE fallback for multi-byte accents.
SHORT_CIRCUIT_MAX_TOKENS_PER_CHARACTER = 2

# Characters per token beyond which a chunk counts as over budget without being counted. Also the hard cap on every
# piece the limiter emits: the splitter measures in tiktoken, which packs a run of `_`, `-` or `.` at ~64 characters
# per token where bge-m3 spends one token per ~16, so a form's fill-in blanks leave it as one piece many times the
# budget. Measured against a live bge-m3, a full-size piece costs ~1.8k tokens as blanks and ~5.7k as German prose.
MAX_CHARACTERS_PER_TOKEN = 4


class TextChunkSizeLimiter:
    """
    Last line of defence before nodes reach the embedding model.

    Every branch that produces a chunk (text, table, table-parse fallback, figure) funnels through here, so a
    branch that forgets its own budget cannot emit a node the embedding model will reject. Enforcing this once
    at the choke point is deliberate: the unbounded table fallback and the unbounded figure branch were both
    introduced without a size check, and per-branch guards would leave the next branch just as exposed.
    """

    def __init__(self, max_tokens: int, token_counter: Callable[[str], int]) -> None:
        self.max_tokens = max_tokens
        self.token_counter = token_counter
        self.splitter = SentenceSplitter(chunk_size=max_tokens, chunk_overlap=0)
        self.max_characters = max_tokens * MAX_CHARACTERS_PER_TOKEN

    def enforce(self, chunks: list[TextChunk]) -> list[TextChunk]:
        limited: list[TextChunk] = []
        for chunk in chunks:
            if self._within_budget(chunk.content):
                limited.append(chunk)
            else:
                limited.extend(
                    TextChunk(piece, chunk.content_type)
                    for split in self.splitter.split_text(chunk.content)
                    for piece in self._cap_characters(split)
                )
        return limited

    def _cap_characters(self, text: str) -> list[str]:
        """The splitter's pieces are sized in tiktoken, so one that tiktoken undercounts is cut at the character cap."""
        return [text[start : start + self.max_characters] for start in range(0, len(text), self.max_characters)]

    def _within_budget(self, content: str) -> bool:
        """
        Short-circuit on character count before paying for a token count.

        `token_counter` is a LiteLLM round trip per call, and nearly every chunk arriving here is a ~512-token
        split that cannot possibly breach the ceiling. The short-circuit is an estimate, not exact: a chunk
        comfortably under budget / SHORT_CIRCUIT_MAX_TOKENS_PER_CHARACTER skips the real count; anything past
        4x the budget is rejected without one either, since no tokenizer this routes through produces more
        tokens than it has characters.
        """
        if len(content) <= self.max_tokens // SHORT_CIRCUIT_MAX_TOKENS_PER_CHARACTER:
            return True
        if len(content) > self.max_characters:
            return False
        return self.token_counter(content) <= self.max_tokens
