"""Text chunker for the GLiNER recognizer that starts every chunk at the beginning of a word.

Presidio's CharacterBasedTextChunker (2.2.364) ends a chunk at a word boundary but starts the next one exactly
`chunk_overlap` characters earlier, which is usually inside a word. GLiNER then reads the word's tail as a word of its
own and tags fragments such as "nne" (from "Nenne") as PERSON. Moving the start forward to the next word keeps the
overlap at word granularity, so a value cut by the previous chunk's end is still seen whole by one of the two chunks.
"""

from presidio_analyzer.chunkers import CharacterBasedTextChunker
from presidio_analyzer.chunkers.base_chunker import TextChunk


class WordAlignedTextChunker(CharacterBasedTextChunker):
    """CharacterBasedTextChunker whose chunks start right after a boundary character, never inside a word."""

    def chunk(self, text: str) -> list[TextChunk]:
        chunks: list[TextChunk] = []
        start = 0
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            while end < len(text) and text[end] not in self.boundary_chars:
                end += 1
            chunks.append(TextChunk(text=text[start:end], start=start, end=end))
            if end >= len(text):
                break
            start = end - self.chunk_overlap
            while start < end and text[start - 1] not in self.boundary_chars:
                start += 1
        return chunks
