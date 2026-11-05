import json
import re
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Any, ClassVar, Self

import sentencepiece
from llama_index.core.utils import get_tokenizer
from pydantic import BaseModel, ConfigDict

VENDORED_DIRECTORY = Path(__file__).parent / "vendored"
FALLBACK_TOKENIZER_ID = "cl100k_base"
TOKENIZER_ID_PATTERN = re.compile(r"[a-z0-9][a-z0-9-]*")

# sentencepiece drops trailing whitespace the provider's tokenizer.json keeps, so on such input it counts exactly one
# token fewer; measured against 20,000 repository snippets, never two. Adding the one back makes it never undercount.
COUNT_MARGIN_BY_FORMAT: dict[str, int] = {"sentencepiece": 1}


class ModelTokenizer(BaseModel):
    """
    One loaded tokenizer, counting text the way the model that owns it spends its window.

    Content is counted without special tokens: what a model adds around an input is a fact about the model (an
    embedder adds two, a reranker four per pair), so callers take it from the model's declaration instead.
    """

    model_config = ConfigDict(frozen=True)

    tokenizer_id: str
    count_margin: int
    encode_without_specials: Callable[[str], list[int]]

    _shared: ClassVar[dict[str, "ModelTokenizer"]] = {}
    _loading: ClassVar[threading.Lock] = threading.Lock()

    def count(self, text: str) -> int:
        return len(self.encode_without_specials(text)) + self.count_margin

    @classmethod
    def shared(cls, tokenizer_id: str) -> Self:
        """Loaded once per process: a tokenizer costs tens of MiB, and concurrent callers in threads would otherwise
        each load their own copy."""
        with cls._loading:
            if tokenizer_id not in cls._shared:
                cls._shared[tokenizer_id] = (
                    cls.tiktoken_fallback()
                    if tokenizer_id == FALLBACK_TOKENIZER_ID
                    else cls.from_vendored(tokenizer_id)
                )
            return cls._shared[tokenizer_id]

    @classmethod
    def tiktoken_fallback(cls) -> Self:
        """What every count used before models declared their tokenizer, kept for the models that still do not."""
        return cls(tokenizer_id=FALLBACK_TOKENIZER_ID, count_margin=0, encode_without_specials=get_tokenizer())

    @classmethod
    def from_vendored(cls, tokenizer_id: str) -> Self:
        source = cls.vendored_source(tokenizer_id)
        match source["format"]:
            case "sentencepiece":
                processor = sentencepiece.SentencePieceProcessor(
                    model_file=str(cls.vendored_directory(tokenizer_id) / source["file"])
                )
                encode = processor.encode
            case unknown_format:
                raise ValueError(f"Tokenizer '{tokenizer_id}' has an unsupported format '{unknown_format}'")
        return cls(
            tokenizer_id=tokenizer_id,
            count_margin=COUNT_MARGIN_BY_FORMAT.get(source["format"], 0),
            encode_without_specials=encode,
        )

    @classmethod
    def vendored_source(cls, tokenizer_id: str) -> dict[str, Any]:
        source_file = cls.vendored_directory(tokenizer_id) / "SOURCE.json"
        if not source_file.is_file():
            raise ValueError(f"Tokenizer '{tokenizer_id}' is not vendored under {VENDORED_DIRECTORY}")
        return json.loads(source_file.read_text(encoding="utf-8"))

    @staticmethod
    def is_vendored(tokenizer_id: str) -> bool:
        return (ModelTokenizer.vendored_directory(tokenizer_id) / "SOURCE.json").is_file()

    @staticmethod
    def vendored_directory(tokenizer_id: str) -> Path:
        """The id comes from the LiteLLM config, so it may only name a folder directly under `vendored/`."""
        if not TOKENIZER_ID_PATTERN.fullmatch(tokenizer_id):
            raise ValueError(f"Tokenizer id '{tokenizer_id}' must be lowercase letters, digits and dashes")
        return VENDORED_DIRECTORY / tokenizer_id.replace("-", "_")
