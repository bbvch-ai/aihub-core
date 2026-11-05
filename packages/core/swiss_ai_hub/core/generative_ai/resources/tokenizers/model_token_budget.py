import logging
import threading
from typing import Annotated, Any, ClassVar, Self

from pydantic import BaseModel, ConfigDict, Field

from swiss_ai_hub.core.generative_ai.resources.tokenizers.model_tokenizer import FALLBACK_TOKENIZER_ID, ModelTokenizer

logger = logging.getLogger(__name__)

DEFAULT_MAX_INPUT_TOKENS = 8192
TOKENIZER_KEY = "aihub_tokenizer"
INPUT_OVERHEAD_KEY = "aihub_input_overhead_tokens"
WARNED_MODES = frozenset({"embedding", "rerank"})


class ModelTokenBudget(BaseModel):
    """
    What a budget site needs to know about one LiteLLM model: how to count for it, its window and what it adds to
    every input.

    Built from `model_info` the caller already holds, so it never goes over the network. A model whose LiteLLM entry
    declares no `aihub_tokenizer` keeps the tiktoken count every site used before (`exact` is false), and the site
    keeps the safety factor that count needs.
    """

    model_config = ConfigDict(frozen=True)

    model_name: str
    tokenizer_id: Annotated[str, Field(description="Vendored tokenizer id, or the tiktoken fallback's.")]
    max_input_tokens: Annotated[int, Field(gt=0)]
    input_overhead_tokens: Annotated[int, Field(ge=0, description="Special tokens the model adds per input.")] = 0
    exact: bool

    _warned_models: ClassVar[set[str]] = set()
    _warning: ClassVar[threading.Lock] = threading.Lock()

    @property
    def tokenizer(self) -> ModelTokenizer:
        """Loaded on first use, so a process that never counts for this model never pays for its tokenizer."""
        return ModelTokenizer.shared(self.tokenizer_id)

    @property
    def usable_input_tokens(self) -> int:
        return self.max_input_tokens - self.input_overhead_tokens

    def count_with_overhead(self, text: str) -> int:
        return self.tokenizer.count(text) + self.input_overhead_tokens

    @classmethod
    def for_model(
        cls,
        model_name: str,
        model_info: Annotated[dict[str, Any], "The `model_info` block of the model's LiteLLM entry"],
        max_input_tokens: Annotated[int | None, "An explicit window, winning over the declared one"] = None,
    ) -> Self:
        window = max_input_tokens or model_info.get("max_input_tokens") or DEFAULT_MAX_INPUT_TOKENS
        tokenizer_id = model_info.get(TOKENIZER_KEY)
        if tokenizer_id is None:
            cls._warn_once_if_embedding_model(model_name, model_info.get("mode"))
            return cls.tiktoken_fallback(window, model_name)
        if not ModelTokenizer.is_vendored(tokenizer_id):
            raise ValueError(f"Model '{model_name}' declares {TOKENIZER_KEY} '{tokenizer_id}', which is not vendored")
        if INPUT_OVERHEAD_KEY not in model_info:
            raise ValueError(f"Model '{model_name}' declares {TOKENIZER_KEY} without {INPUT_OVERHEAD_KEY}")
        return cls(
            model_name=model_name,
            tokenizer_id=tokenizer_id,
            max_input_tokens=window,
            input_overhead_tokens=model_info[INPUT_OVERHEAD_KEY],
            exact=True,
        )

    @classmethod
    def tiktoken_fallback(cls, max_input_tokens: int = DEFAULT_MAX_INPUT_TOKENS, model_name: str = "") -> Self:
        return cls(
            model_name=model_name, tokenizer_id=FALLBACK_TOKENIZER_ID, max_input_tokens=max_input_tokens, exact=False
        )

    @classmethod
    def _warn_once_if_embedding_model(cls, model_name: str, mode: str | None) -> None:
        """Every chat model is undeclared for now and must stay quiet; an embedder or reranker without its tokenizer
        is something an admin should see, but once, not on every chunk."""
        if mode not in WARNED_MODES:
            return
        with cls._warning:
            if model_name in cls._warned_models:
                return
            cls._warned_models.add(model_name)
        logger.warning(
            "Model '%s' (%s) declares no %s in LiteLLM: its inputs are sized with tiktoken and a safety factor, "
            "not counted exactly",
            model_name,
            mode,
            TOKENIZER_KEY,
        )
