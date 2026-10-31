from collections.abc import Callable
from typing import Annotated

from llama_index.core.node_parser import SentenceSplitter

from swiss_ai_hub.core.generative_ai.document.parsers.text_chunk import TextChunk
from swiss_ai_hub.core.generative_ai.resources.tokenizers.measured_text_cut import MeasuredTextCut

# Worst-case tokens per character assumed by `_within_budget`'s accept short-circuit -- see the identical
# constant and rationale in recursive_summary_parser.py. Kept separate since the two budgets are independent
# decisions that happen to share this assumption: deployments process Latin-script EU-language content, not
# CJK, so a character costs at most ~2 tokens even under byte-level BPE fallback for multi-byte accents.
SHORT_CIRCUIT_MAX_TOKENS_PER_CHARACTER = 2

# Characters per token beyond which a chunk counts as over budget without being counted. Also the hard cap on every
# piece the limiter emits when it cannot count in the model's own tokens: the splitter then measures in tiktoken,
# which packs a run of `_`, `-` or `.` at ~64 characters per token where bge-m3 spends one token per ~16, so a form's
# fill-in blanks leave it as one piece many times the budget. Measured against a live bge-m3, a full-size piece costs
# ~1.8k tokens as blanks and ~5.7k as German prose.
MAX_CHARACTERS_PER_TOKEN = 4

# SentenceSplitter sums the counts of pieces it encoded one by one, and a piece encoded alone gets the word-initial
# vocabulary the joined text does not. At a chunk size of 2048 this repository's dense import modules came out at up
# to 2166 bge-m3 tokens (core/infrastructure/__init__.py; prose, tables and LaTeX stay under 2048). A piece over budget
# is therefore split again, smaller by the measured overshoot plus this, and cut by measured characters if it still is.
RESPLIT_MARGIN_TOKENS = 8
MAX_RESPLIT_ROUNDS = 3


class TextChunkSizeLimiter:
    """
    Last line of defence before nodes reach the embedding model.

    Every branch that produces a chunk (text, table, table-parse fallback, figure) funnels through here, so a
    branch that forgets its own budget cannot emit a node the embedding model will reject. Enforcing this once
    at the choke point is deliberate: the unbounded table fallback and the unbounded figure branch were both
    introduced without a size check, and per-branch guards would leave the next branch just as exposed.

    With the model's own tokenizer (`encode` given) every piece it emits is counted exactly. Without it, the count is
    an estimate, so character caps bound what the estimate can miss.
    """

    def __init__(
        self,
        max_tokens: int,
        token_counter: Callable[[str], int],
        encode: Annotated[
            Callable[[str], list[int]] | None, "The model's own encoding without special tokens, for exact splits"
        ] = None,
    ) -> None:
        self.max_tokens = max_tokens
        self.token_counter = token_counter
        self.encode = encode
        self.splitter = self._splitter(max_tokens)
        self.max_characters = max_tokens * MAX_CHARACTERS_PER_TOKEN

    @property
    def exact(self) -> bool:
        return self.encode is not None

    def enforce(self, chunks: list[TextChunk]) -> list[TextChunk]:
        limited: list[TextChunk] = []
        for chunk in chunks:
            if self._within_budget(chunk.content):
                limited.append(chunk)
            else:
                limited.extend(TextChunk(piece, chunk.content_type) for piece in self._split(chunk.content))
        return limited

    def _split(self, text: str) -> list[str]:
        if self.exact:
            return [piece for split in self.splitter.split_text(text) for piece in self._fit(split, MAX_RESPLIT_ROUNDS)]
        return [piece for split in self.splitter.split_text(text) for piece in self._cap_characters(split)]

    def _fit(self, piece: str, rounds_left: int) -> list[str]:
        """Re-split a piece the splitter's summed count let through, until every piece measures within budget."""
        measured = self.token_counter(piece)
        if measured <= self.max_tokens:
            return [piece]
        if rounds_left == 0:
            return MeasuredTextCut.pieces(piece, self.max_tokens, self.token_counter)
        smaller = max(1, self.max_tokens * self.max_tokens // measured - RESPLIT_MARGIN_TOKENS)
        return [
            fitted
            for split in self._splitter(smaller).split_text(piece)
            for fitted in self._fit(split, rounds_left - 1)
        ]

    def _splitter(self, chunk_size: int) -> SentenceSplitter:
        return SentenceSplitter(chunk_size=chunk_size, chunk_overlap=0, tokenizer=self.encode)

    def _cap_characters(self, text: str) -> list[str]:
        """The splitter's pieces are sized in tiktoken, so one that tiktoken undercounts is cut at the character cap."""
        return [text[start : start + self.max_characters] for start in range(0, len(text), self.max_characters)]

    def _within_budget(self, content: str) -> bool:
        """
        Short-circuit on character count before paying for a token count, unless the count is exact.

        Without the model's tokenizer the count is an estimate anyway, and nearly every chunk arriving here is a
        ~512-token split that cannot possibly breach the ceiling: a chunk comfortably under
        budget / SHORT_CIRCUIT_MAX_TOKENS_PER_CHARACTER skips the count, and anything past MAX_CHARACTERS_PER_TOKEN
        times the budget is rejected without one. With the model's tokenizer a count is a fraction of a millisecond
        and the only figure that is right, so it is always taken.
        """
        if self.exact:
            return self.token_counter(content) <= self.max_tokens
        if len(content) <= self.max_tokens // SHORT_CIRCUIT_MAX_TOKENS_PER_CHARACTER:
            return True
        if len(content) > self.max_characters:
            return False
        return self.token_counter(content) <= self.max_tokens
