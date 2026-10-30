"""With the embedding model's own tokenizer the limiter must never emit a piece over budget. SentenceSplitter alone
does not guarantee that: it sums the counts of pieces encoded one by one, and Python code came out at 2113 bge-m3
tokens for a chunk size of 2048."""

from pathlib import Path

import pytest

from swiss_ai_hub.core.generative_ai.document.parsers.text_chunk import TextChunk
from swiss_ai_hub.core.generative_ai.document.parsers.text_chunk_size_limiter import TextChunkSizeLimiter
from swiss_ai_hub.core.generative_ai.resources.tokenizers.model_tokenizer import ModelTokenizer
from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import NODE_CONTENT_TYPE_FIGURE, NODE_CONTENT_TYPE_TEXT

BUDGET = 2048
CORE_SOURCES = Path(__file__).resolve().parents[4]


def _repository_python() -> str:
    files = sorted((CORE_SOURCES / "document" / "parsers").glob("*.py"))
    return "\n\n".join(path.read_text(encoding="utf-8") for path in files)


def _numeric_table() -> str:
    rows = [
        f"| {row} | {row * 3.14159:.5f} | {row * 1000003 % 97:02d} | 2026-{row % 12 + 1:02d}-15 |"
        for row in range(2000)
    ]
    return "| id | value | check | date |\n|---|---|---|---|\n" + "\n".join(rows)


CONTENT = {
    "repository python": _repository_python(),
    "numeric table": _numeric_table(),
    "latex": r"\begin{equation} \int_0^\infty e^{-x^2} \, dx = \frac{\sqrt{\pi}}{2} \end{equation} " * 600,
    "german": "Die Kündigungsfrist für unbefristete Arbeitsverhältnisse beträgt drei Monate zum Monatsende. " * 600,
    "underscores": "Name: ________________________  Datum: ____________  Unterschrift: ______________\n" * 600,
    "one long word": "x" * 100_000,
}


@pytest.fixture(scope="module")
def limiter() -> TextChunkSizeLimiter:
    bge_m3 = ModelTokenizer.shared("bge-m3")
    return TextChunkSizeLimiter(BUDGET, bge_m3.count, encode=bge_m3.encode_without_specials)


@pytest.mark.parametrize("content", CONTENT.values(), ids=CONTENT.keys())
def test_every_piece_fits_under_the_exact_count(limiter: TextChunkSizeLimiter, content: str) -> None:
    pieces = limiter.enforce([TextChunk(content, NODE_CONTENT_TYPE_FIGURE)])

    counts = [limiter.token_counter(piece.content) for piece in pieces]
    assert len(pieces) > 1
    assert max(counts) <= BUDGET
    assert all(piece.content_type == NODE_CONTENT_TYPE_FIGURE for piece in pieces)


def test_exact_count_is_taken_even_for_short_chunks(limiter: TextChunkSizeLimiter) -> None:
    """No character short-circuit: a short chunk of blanks is still counted, never assumed to fit."""
    chunk = TextChunk("a short sentence", NODE_CONTENT_TYPE_TEXT)

    assert limiter.enforce([chunk]) == [chunk]


def test_pieces_keep_the_text_without_decoding_tokens(limiter: TextChunkSizeLimiter) -> None:
    content = CONTENT["one long word"]

    pieces = limiter.enforce([TextChunk(content, NODE_CONTENT_TYPE_TEXT)])

    assert "".join(piece.content for piece in pieces) == content
