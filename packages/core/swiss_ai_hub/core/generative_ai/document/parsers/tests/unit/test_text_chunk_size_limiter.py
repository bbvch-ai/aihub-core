"""Tests for the hard ceiling applied to every chunk before it becomes a node."""

from swiss_ai_hub.core.generative_ai.document.parsers.text_chunk import TextChunk
from swiss_ai_hub.core.generative_ai.document.parsers.text_chunk_size_limiter import TextChunkSizeLimiter
from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import (
    NODE_CONTENT_TYPE_FIGURE,
    NODE_CONTENT_TYPE_TABLE,
    NODE_CONTENT_TYPE_TEXT,
)


def word_count(text: str) -> int:
    return len(text.split())


class TestTextChunkSizeLimiter:
    def test_chunk_within_budget_passes_through_unchanged(self) -> None:
        limiter = TextChunkSizeLimiter(max_tokens=100, token_counter=word_count)
        chunk = TextChunk("a short sentence", NODE_CONTENT_TYPE_TEXT)

        assert limiter.enforce([chunk]) == [chunk]

    def test_oversized_chunk_is_split(self) -> None:
        limiter = TextChunkSizeLimiter(max_tokens=50, token_counter=word_count)
        chunk = TextChunk(" ".join(f"word{i}" for i in range(500)), NODE_CONTENT_TYPE_TEXT)

        result = limiter.enforce([chunk])

        assert len(result) > 1

    def test_every_resulting_chunk_is_within_budget(self) -> None:
        limiter = TextChunkSizeLimiter(max_tokens=50, token_counter=word_count)
        chunk = TextChunk(" ".join(f"word{i}" for i in range(500)), NODE_CONTENT_TYPE_TEXT)

        result = limiter.enforce([chunk])

        assert all(word_count(part.content) <= 50 for part in result)

    def test_unstructured_run_still_converges(self) -> None:
        """The failing document was one table stripped to a digit run with no sentence boundary to split on."""
        limiter = TextChunkSizeLimiter(max_tokens=50, token_counter=word_count)
        digits = " ".join(str(number) for number in range(2000))

        result = limiter.enforce([TextChunk(digits, NODE_CONTENT_TYPE_TABLE)])

        assert all(word_count(part.content) <= 50 for part in result)

    def test_content_type_is_preserved_across_splits(self) -> None:
        limiter = TextChunkSizeLimiter(max_tokens=50, token_counter=word_count)
        chunk = TextChunk(" ".join(f"word{i}" for i in range(500)), NODE_CONTENT_TYPE_FIGURE)

        result = limiter.enforce([chunk])

        assert {part.content_type for part in result} == {NODE_CONTENT_TYPE_FIGURE}

    def test_mixed_chunks_only_split_the_oversized_one(self) -> None:
        limiter = TextChunkSizeLimiter(max_tokens=50, token_counter=word_count)
        small = TextChunk("small", NODE_CONTENT_TYPE_TEXT)
        large = TextChunk(" ".join(f"word{i}" for i in range(500)), NODE_CONTENT_TYPE_TABLE)

        result = limiter.enforce([small, large])

        assert result[0] == small
        assert len(result) > 2

    def test_empty_input_returns_empty(self) -> None:
        limiter = TextChunkSizeLimiter(max_tokens=50, token_counter=word_count)

        assert limiter.enforce([]) == []
