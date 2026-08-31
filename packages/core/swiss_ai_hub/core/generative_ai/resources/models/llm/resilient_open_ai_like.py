import logging
from collections.abc import Sequence
from typing import Any, ClassVar, override

from llama_index.core.base.llms.types import ChatMessage, ChatResponseAsyncGen, ChatResponseGen
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

# Usage on the final streamed chunk lets ``TokenCountingHandler`` read the gateway's real prompt/completion
# counts instead of re-tokenizing the whole chat history locally. ``stream_options`` is a standard OpenAI
# parameter, so LiteLLM forwards it to the upstream endpoint even with ``drop_params`` enabled — an
# OpenAI-compatible endpoint that doesn't implement it answers 400 and would otherwise break every streamed
# response for that model. Like ``chat_template_kwargs`` the rejection arrives before the first chunk, so
# the plain retry is safe and no partial output reaches the user twice.
_USAGE_ON_FINAL_CHUNK = {"stream_options": {"include_usage": True}}


class ResilientOpenAILike(OpenAILike):
    """
    OpenAILike hardened for the reasoning models served by Infomaniak.

    On the ``response_format`` structured-output path (``should_use_structured_outputs``) it disables
    reasoning so the model returns parseable JSON, falling back to a plain request for models that reject
    ``chat_template_kwargs``. Any remaining malformed output is retried a few times before the error
    propagates; callers that must not fail the run additionally catch the final error and fall back to a
    safe default. Streamed calls additionally request usage on the final chunk, falling back to a plain
    stream for endpoints that reject ``stream_options``. Mirrors the provider-quirk subclassing of
    ``PatchedOpenAILLM``.
    """

    _models_rejecting_stream_options: ClassVar[set[str]] = set()

    @override
    async def astream_chat(self, messages: Sequence[ChatMessage], **kwargs: Any) -> ChatResponseAsyncGen:
        if self.model in ResilientOpenAILike._models_rejecting_stream_options:
            return await super().astream_chat(messages, **kwargs)
        return self._astream_chat_requesting_usage(messages, **kwargs)

    async def _astream_chat_requesting_usage(
        self, messages: Sequence[ChatMessage], **kwargs: Any
    ) -> ChatResponseAsyncGen:
        streamed_any_chunk = False
        try:
            async for chunk in await super().astream_chat(messages, **{**_USAGE_ON_FINAL_CHUNK, **kwargs}):
                streamed_any_chunk = True
                yield chunk
            return
        except BadRequestError as stream_options_rejected:
            if streamed_any_chunk:
                raise
            self._remember_stream_options_rejection(stream_options_rejected)

        async for chunk in await super().astream_chat(messages, **kwargs):
            yield chunk

    @override
    def stream_chat(self, messages: Sequence[ChatMessage], **kwargs: Any) -> ChatResponseGen:
        if self.model in ResilientOpenAILike._models_rejecting_stream_options:
            return super().stream_chat(messages, **kwargs)
        return self._stream_chat_requesting_usage(messages, **kwargs)

    def _stream_chat_requesting_usage(self, messages: Sequence[ChatMessage], **kwargs: Any) -> ChatResponseGen:
        streamed_any_chunk = False
        try:
            for chunk in super().stream_chat(messages, **{**_USAGE_ON_FINAL_CHUNK, **kwargs}):
                streamed_any_chunk = True
                yield chunk
            return
        except BadRequestError as stream_options_rejected:
            if streamed_any_chunk:
                raise
            self._remember_stream_options_rejection(stream_options_rejected)

        yield from super().stream_chat(messages, **kwargs)

    def _remember_stream_options_rejection(self, rejection: BadRequestError) -> None:
        """Stream plainly for the rest of the process, so a rejecting endpoint costs one extra request in total."""
        ResilientOpenAILike._models_rejecting_stream_options.add(self.model)
        logger.warning(
            "Model %s rejected stream_options.include_usage (%s); streaming without gateway usage reporting "
            "and falling back to local token counting for this model.",
            self.model,
            rejection,
        )

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
