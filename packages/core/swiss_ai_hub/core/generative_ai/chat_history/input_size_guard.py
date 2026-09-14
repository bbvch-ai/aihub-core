import logging
from collections.abc import Callable

from httpx import HTTPError
from llama_index.core.base.llms.types import ChatMessage

from swiss_ai_hub.core.generative_ai.resources.models.llm.llm_config import LLMConfig

logger = logging.getLogger(__name__)

# Absorbs what the count cannot know: the tokenizer reached through `LLMConfig.token_counter` is tiktoken, not the
# tokenizer of whichever model LiteLLM routes to, and the chat envelope around the rendered messages costs tokens of
# its own. Same value and same reasoning as SUMMARIZATION_BUDGET_SAFETY_FACTOR in `recursive_summary_parser` and
# BUDGET_SAFETY_FACTOR in the agent package's `imap/token_budget`.
BUDGET_SAFETY_FACTOR = 0.85

# llama-index's own per-image estimate, taken as a constant. Asking `ImageBlock.aestimate_tokens` for it would make
# the block resolve itself -- downloading the image -- to return this same number, and a guard that exists to avoid a
# wasted model call must not spend a network round trip deciding.
IMAGE_BLOCK_TOKEN_ESTIMATE = 2125


def usable_input_budget(llm_configs: list[LLMConfig | None]) -> int | None:
    """The largest prompt these models will all accept, or None when no window can be established.

    The narrowest window wins: one prompt is built once and handed to whichever model each step uses, so a budget
    that fitted only the widest would still fail on the others. Returns None rather than raising -- a model missing
    from LiteLLM, or an entry without a declared window, must leave the run behaving exactly as it did before this
    guard existed rather than failing it.
    """
    windows = []
    for llm_config in llm_configs:
        if llm_config is None:
            continue
        try:
            window = llm_config.max_input_tokens
        except (ValueError, KeyError, TypeError, HTTPError) as window_lookup_failure:
            logger.warning(
                "[input-size-guard] no context window for %s (%s); skipping the size check.",
                llm_config.model_name,
                type(window_lookup_failure).__name__,
            )
            return None
        if window is None:
            logger.warning(
                "[input-size-guard] %s declares no max_input_tokens; skipping the size check.", llm_config.model_name
            )
            return None
        windows.append(window)

    return int(min(windows) * BUDGET_SAFETY_FACTOR) if windows else None


def estimate_prompt_tokens(messages: list[ChatMessage], token_counter: Callable[[str], list[int]]) -> int:
    """Estimate what `messages` cost the model, counting text directly and non-text blocks at a flat rate.

    Deliberately not `TokenCounter.estimate_tokens_in_messages`: that routes every message through `asyncio_run`, and
    resolves image blocks over the network purely to return a constant.
    """
    tokens = 0
    for message in messages:
        tokens += len(token_counter(message.role.value))
        for block in message.blocks:
            if getattr(block, "block_type", "text") == "text":
                tokens += len(token_counter(getattr(block, "text", "") or ""))
            else:
                tokens += IMAGE_BLOCK_TOKEN_ESTIMATE
    return tokens
