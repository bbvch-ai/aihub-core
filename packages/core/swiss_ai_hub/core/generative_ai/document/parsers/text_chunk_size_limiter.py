from collections.abc import Callable

from llama_index.core.node_parser import SentenceSplitter

from swiss_ai_hub.core.generative_ai.document.parsers.text_chunk import TextChunk

# Worst-case tokens per character assumed by `_within_budget`'s accept short-circuit -- see the identical
# constant and rationale in recursive_summary_parser.py. Kept separate since the two budgets are independent
# decisions that happen to share this assumption: deployments process Latin-script EU-language content, not
# CJK, so a character costs at most ~2 tokens even under byte-level BPE fallback for multi-byte accents.
SHORT_CIRCUIT_MAX_TOKENS_PER_CHARACTER = 2


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

    def enforce(self, chunks: list[TextChunk]) -> list[TextChunk]:
        limited: list[TextChunk] = []
        for chunk in chunks:
            if self._within_budget(chunk.content):
                limited.append(chunk)
            else:
                limited.extend(
                    TextChunk(split, chunk.content_type) for split in self.splitter.split_text(chunk.content)
                )
        return limited

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
        if len(content) > self.max_tokens * 4:
            return False
        return self.token_counter(content) <= self.max_tokens
