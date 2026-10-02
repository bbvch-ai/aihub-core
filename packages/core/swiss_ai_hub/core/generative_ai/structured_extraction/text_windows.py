from collections.abc import Callable

from llama_index.core.node_parser import SentenceSplitter


class TextWindows:
    """Splits a document too long for one model call into overlapping windows.

    The overlap is what keeps a record that straddles a boundary whole in at least one window; the duplicates it
    creates are removed afterwards by `RecordMerger`.
    """

    @staticmethod
    def split(
        text: str, window_tokens: int, overlap_tokens: int, token_counter: Callable[[str], list[int]]
    ) -> list[str]:
        if not text.strip():
            return []
        if len(token_counter(text)) <= window_tokens:
            return [text]
        splitter = SentenceSplitter(chunk_size=window_tokens, chunk_overlap=overlap_tokens, tokenizer=token_counter)
        return splitter.split_text(text)
