from collections.abc import Callable

from llama_index.core.node_parser import SentenceSplitter

from swiss_ai_hub.core.generative_ai.document.parsers.text_chunk import TextChunk


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
        split that cannot possibly breach the ceiling. A token is never fewer than one character, so a chunk
        shorter than the budget is under it by construction - the check is exact, not an estimate.
        """
        return len(content) <= self.max_tokens or self.token_counter(content) <= self.max_tokens
