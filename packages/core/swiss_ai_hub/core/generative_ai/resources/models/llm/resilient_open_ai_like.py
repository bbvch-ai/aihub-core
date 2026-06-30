import logging
from typing import Any, override

from llama_index.llms.openai_like import OpenAILike
from pydantic import ValidationError

logger = logging.getLogger(__name__)

STRUCTURED_OUTPUT_ATTEMPTS = 3


class ResilientOpenAILike(OpenAILike):
    """
    OpenAILike that retries structured prediction against flaky reasoning models on Infomaniak.

    Reasoning models there intermittently emit unparseable structured output (empty tool calls,
    truncated/fenced JSON, omitted fields); a fresh generation often parses, so we retry a few times
    before letting the error propagate. Callers that must not fail the run additionally catch the
    final error and fall back to a safe default. Mirrors the provider-quirk subclassing of
    ``PatchedOpenAILLM``.
    """

    @override
    async def astructured_predict(self, *args: Any, **kwargs: Any) -> Any:
        for attempt in range(1, STRUCTURED_OUTPUT_ATTEMPTS + 1):
            try:
                return await super().astructured_predict(*args, **kwargs)
            except (ValidationError, ValueError) as malformed_structured_output:
                logger.warning(
                    "Structured prediction returned malformed output (attempt %d/%d): %s",
                    attempt,
                    STRUCTURED_OUTPUT_ATTEMPTS,
                    malformed_structured_output,
                )
                if attempt == STRUCTURED_OUTPUT_ATTEMPTS:
                    raise
        raise RuntimeError("STRUCTURED_OUTPUT_ATTEMPTS must be >= 1.")

    @override
    def structured_predict(self, *args: Any, **kwargs: Any) -> Any:
        for attempt in range(1, STRUCTURED_OUTPUT_ATTEMPTS + 1):
            try:
                return super().structured_predict(*args, **kwargs)
            except (ValidationError, ValueError) as malformed_structured_output:
                logger.warning(
                    "Structured prediction returned malformed output (attempt %d/%d): %s",
                    attempt,
                    STRUCTURED_OUTPUT_ATTEMPTS,
                    malformed_structured_output,
                )
                if attempt == STRUCTURED_OUTPUT_ATTEMPTS:
                    raise
        raise RuntimeError("STRUCTURED_OUTPUT_ATTEMPTS must be >= 1.")
