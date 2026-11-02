import logging
from collections.abc import Callable
from typing import Annotated

from llama_index.core.utils import get_tokenizer

from swiss_ai_hub.core.generative_ai.resources.models.llm.embedding_model_config import EmbeddingModelConfig
from swiss_ai_hub.core.generative_ai.resources.models.llm.reranking_model_config import RerankingModelConfig
from swiss_ai_hub.core.generative_ai.resources.tokenizers.measured_text_cut import MeasuredTextCut
from swiss_ai_hub.core.generative_ai.resources.tokenizers.model_token_budget import ModelTokenBudget

logger = logging.getLogger(__name__)

# Only for a model that declares no tokenizer: its budget is counted in tiktoken, which undercounts bge-m3 by up to
# 1.45x on code and 1.31x on whitespace-heavy text, while real English measures 1.00-1.12x (the 1.6x once quoted
# here came from a synthetic sample). Half the window covers that worst case with room to spare. A model that
# declares its tokenizer is counted exactly and gets its whole window.
QUERY_BUDGET_SAFETY_FACTOR = 0.5

# Smallest window we assume any deployed embedder accepts. Only used to decide when a query is short enough
# to skip resolving the real window, so it must never exceed a configured model's actual window.
MINIMUM_EMBEDDING_MAX_INPUT_TOKENS = 512


class EmbeddingQueryClamp:
    """
    Fits a query into the embedding model's window. Chat clients inline whole attached documents into the
    user message, and an embedding model rejects an oversized input with a 400 instead of truncating it.

    Counting a long query costs tens of milliseconds and resolving the window may go over the network once per
    process, so async callers run `clamp` in a thread.
    """

    @staticmethod
    def token_limit(budget: ModelTokenBudget) -> int:
        if budget.exact:
            return budget.usable_input_tokens
        return max(1, int(budget.max_input_tokens * QUERY_BUDGET_SAFETY_FACTOR))

    @classmethod
    def clamp(
        cls,
        query: str,
        model_name: str,
        max_input_tokens: Annotated[int | None, "An explicit window, winning over the declared one"] = None,
    ) -> str:
        """
        The cheap check counts tiktoken tokens rather than characters: a character is not an upper bound on tokens
        (a ZWJ emoji sequence costs 7). It compares against half the smallest window we support, which even the
        worst tiktoken undercount measured (1.65x) keeps inside any model's window, so a query that fits it returns
        without resolving the model.
        """
        if cls.fits_any_window(query, max_input_tokens):
            return query
        budget = EmbeddingModelConfig(model_name=model_name).token_budget(max_input_tokens)
        return cls.clamp_to(query, cls.token_limit(budget), budget.tokenizer.count)

    @classmethod
    def clamp_for_rerank(
        cls,
        query: str,
        reranking_model_name: str,
        document_room: Annotated[int, "Tokens kept free for the document each query is paired with"],
    ) -> str:
        """For a reranker reached outside `rerank_nodes`, which sizes each request itself: mem0 pairs the query with
        every memory in one window, so a query filling it leaves a memory no room and the whole rerank is refused."""
        if cls.fits_any_window(query):
            return query
        budget = RerankingModelConfig(model_name=reranking_model_name).token_budget()
        limit = cls.token_limit(budget) - (document_room if budget.exact else 0)
        return cls.clamp_to(query, limit, budget.tokenizer.count)

    @staticmethod
    def fits_any_window(query: str, max_input_tokens: int | None = None) -> bool:
        return len(get_tokenizer()(query)) <= int(
            (max_input_tokens or MINIMUM_EMBEDDING_MAX_INPUT_TOKENS) * QUERY_BUDGET_SAFETY_FACTOR
        )

    @staticmethod
    def clamp_to(query: str, limit: int, count: Callable[[str], int]) -> str:
        """The tail is kept: chat clients inline documents before the user's question, so that is where it lives."""
        original_tokens = count(query)
        if original_tokens <= limit:
            return query
        clamped = MeasuredTextCut.longest_fitting_tail(query, limit, count)
        logger.warning(
            "Query exceeds the embedding budget, truncating: %d -> %d tokens (%d -> %d characters, limit %d)",
            original_tokens,
            count(clamped),
            len(query),
            len(clamped),
            limit,
        )
        return clamped
