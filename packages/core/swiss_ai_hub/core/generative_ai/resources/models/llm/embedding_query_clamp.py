import logging
from collections.abc import Callable

from llama_index.core.utils import get_tokenizer

from swiss_ai_hub.core.generative_ai.resources.models.llm.embedding_model_config import EmbeddingModelConfig

logger = logging.getLogger(__name__)

DEFAULT_EMBEDDING_MAX_INPUT_TOKENS = 8192

# We can only count tiktoken tokens locally, but the budget is spent in the embedder's own tokenizer, and
# tiktoken undercounts. Measured against a live bge-m3: English 1.60x (8101 -> 12963), French 1.00x, German
# and Chinese below 1. The factor has to cover the worst case, so it tolerates a 2x undercount. Deliberately
# not the 0.85 that markdown_structural_node_parser uses for chunking: at the measured English ratio 0.85
# leaves a full-size input at ~1.9x its real budget. Raising this needs the same measurement against
# whatever model the deployment runs.
QUERY_BUDGET_SAFETY_FACTOR = 0.5

# Smallest window we assume any deployed embedder accepts. Only used to decide when a query is short enough
# to skip resolving the real window, so it must never exceed a configured model's actual window.
MINIMUM_EMBEDDING_MAX_INPUT_TOKENS = 512


class EmbeddingQueryClamp:
    """
    Fits a query into the embedding model's window. Chat clients inline whole attached documents into the
    user message, and an embedding model rejects an oversized input with a 400 instead of truncating it.

    Also guards rerank calls: the window is resolved by model name, and a reranker spends its own window on
    the query plus one document per pair, so the clamped query must leave room for a chunk.
    """

    @staticmethod
    def token_limit(model_name: str, max_input_tokens: int | None = None) -> int:
        """An explicit window wins, so a deployment can override a model whose LiteLLM entry is wrong."""
        window = max_input_tokens or (
            EmbeddingModelConfig(model_name=model_name).get_model_info()["model_info"].get("max_input_tokens")
            or DEFAULT_EMBEDDING_MAX_INPUT_TOKENS
        )
        return max(1, int(window * QUERY_BUDGET_SAFETY_FACTOR))

    @staticmethod
    def longest_fitting_tail(query: str, limit: int, tokenizer: Callable[[str], list[int]]) -> str:
        """
        Keep a long suffix within the budget: chat clients inline documents before the user's question, so
        the tail is where the question lives.

        Safety does not rest on suffix token counts being monotonic — under BPE they are not
        ("unbelievable" measures [3, 3, 2, 3, ...]). It rests on `high` only ever being assigned an index
        that measured as fitting, so the returned suffix was measured, never inferred. Non-monotonicity
        costs optimality alone: a slightly longer suffix may also have fit.

        Chosen over a sentence splitter because sentence boundaries buy an embedding vector nothing while
        this hits the budget exactly. It also avoids NLTK punkt, whose corpus loader rejects files with
        st_nlink > 1 — which is what a `uv` venv installs by default, though not what the images ship
        (every app Dockerfile sets UV_LINK_MODE=copy), so that failure is a dev-machine one.
        """
        low, high = 0, len(query)
        while low < high:
            middle = (low + high) // 2
            if len(tokenizer(query[middle:])) <= limit:
                high = middle
            else:
                low = middle + 1
        return query[low:] or query[-1:]

    @classmethod
    def clamp(cls, query: str, model_name: str, max_input_tokens: int | None = None) -> str:
        """
        The cheap check counts tokens rather than characters: a character is not an upper bound on tokens
        (a ZWJ emoji sequence costs 7). It compares against the smallest window we support so a query that
        fits any model returns without resolving the real, possibly remote, limit.
        """
        tokenizer = get_tokenizer()
        original_tokens = len(tokenizer(query))
        resolution_free_budget = int(
            (max_input_tokens or MINIMUM_EMBEDDING_MAX_INPUT_TOKENS) * QUERY_BUDGET_SAFETY_FACTOR
        )
        if original_tokens <= resolution_free_budget:
            return query
        limit = cls.token_limit(model_name, max_input_tokens)
        if original_tokens <= limit:
            return query
        clamped = cls.longest_fitting_tail(query, limit, tokenizer)
        logger.warning(
            "Query exceeds the embedding budget, truncating: %d -> %d tokens (%d -> %d characters, limit %d)",
            original_tokens,
            len(tokenizer(clamped)),
            len(query),
            len(clamped),
            limit,
        )
        return clamped
