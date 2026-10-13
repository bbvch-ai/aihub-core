"""Measuring a prompt against a model's context window, for callers deciding whether to refuse one.

Carries no safety factor, unlike `recursive_summary_parser` and the agent package's `imap/token_budget`. Those shrink
a budget they then *fill*, where over-counting only wastes room; a budget used to refuse a user outright would instead
reject prompts the model accepts. The tokenizer behind `LLMConfig.token_counter` is tiktoken, not the served model's,
and the error runs both ways -- measured against gemma-4-31B-it, 121k tiktoken tokens of Vietnamese fit a declared
100k window on Infomaniak. So the only thing these numbers can settle is whether an input exceeds the window on a
single reading, which no downstream step could rescue. Anything subtler belongs to the model, whose own 400
`ModelGatewayErrorHandler` rewrites into a sentence naming the limit.
"""

import logging
from collections.abc import Callable

from httpx import HTTPError
from llama_index.core.base.llms.types import ChatMessage

from swiss_ai_hub.core.generative_ai.resources.models.llm.llm_config import LLMConfig

logger = logging.getLogger(__name__)

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
        # `model_info` is an untyped dict straight off the gateway, so a window is usable only once it proves to be
        # a positive int. Anything else is "no window established", which fails open like a missing entry.
        if not isinstance(window, int) or isinstance(window, bool) or window <= 0:
            logger.warning(
                "[input-size-guard] %s declares no usable max_input_tokens (%r); skipping the size check.",
                llm_config.model_name,
                window,
            )
            return None
        windows.append(window)

    return min(windows) if windows else None


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
