import logging
from typing import Any, override

from llama_index.llms.openai_like import OpenAILike
from openai import BadRequestError
from pydantic import ValidationError

logger = logging.getLogger(__name__)

STRUCTURED_OUTPUT_ATTEMPTS = 3

# Reasoning models on Infomaniak emit clean JSON via ``response_format`` only with thinking disabled; a
# structured extraction (title, follow-ups, routing) is a trivial task, so reasoning is pure latency and
# the source of the fenced/truncated/omitted-field output the provider otherwise returns. Model families
# read different keys — Qwen3 honours ``enable_thinking`` (and silently ignores ``thinking``, still burning
# ~1k reasoning tokens), other vLLM templates honour ``thinking`` — so send both. Mistral-tokenizer models
# (Ministral) reject ``chat_template_kwargs`` with a 400, so the call falls back to a plain request.
_REASONING_DISABLED = {"chat_template_kwargs": {"thinking": False, "enable_thinking": False}}


class ResilientOpenAILike(OpenAILike):
    """
    OpenAILike hardened for the reasoning models served by Infomaniak.

    On the ``response_format`` structured-output path (``should_use_structured_outputs``) it disables
    reasoning so the model returns parseable JSON, falling back to a plain request for models that reject
    ``chat_template_kwargs``. Any remaining malformed output is retried a few times before the error
    propagates; callers that must not fail the run additionally catch the final error and fall back to a
    safe default. Mirrors the provider-quirk subclassing of ``PatchedOpenAILLM``.
    """

    def _reasoning_disabled_kwargs(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        """Merge thinking-off into the call's ``llm_kwargs.extra_body`` without mutating the caller's dict."""
        llm_kwargs = dict(kwargs.get("llm_kwargs") or {})
        llm_kwargs["extra_body"] = {**llm_kwargs.get("extra_body", {}), **_REASONING_DISABLED}
        return {**kwargs, "llm_kwargs": llm_kwargs}

    @override
    async def astructured_predict(self, *args: Any, **kwargs: Any) -> Any:
        for attempt in range(1, STRUCTURED_OUTPUT_ATTEMPTS + 1):
            try:
                if not self.should_use_structured_outputs:
                    return await super().astructured_predict(*args, **kwargs)
                try:
                    return await super().astructured_predict(*args, **self._reasoning_disabled_kwargs(kwargs))
                except BadRequestError:
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
                if not self.should_use_structured_outputs:
                    return super().structured_predict(*args, **kwargs)
                try:
                    return super().structured_predict(*args, **self._reasoning_disabled_kwargs(kwargs))
                except BadRequestError:
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
