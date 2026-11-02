from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, ClassVar


class GatewayGuardrails:
    """The LiteLLM guardrails the LLM calls of the current task ask the gateway for by name.

    A profile's anonymisation applies to every LLM call of its run, and those calls are built in dozens of places
    that see only the model config. A context variable reaches all of them: the dispatcher sets it around each
    step, the step's awaits, tasks and threads inherit it, and `ResilientOpenAILike` reads it when it assembles
    a request. Code that runs outside the step's context (mem0's own worker threads) is given the names explicitly.
    """

    PII_ANONYMISATION: ClassVar[str] = "pii-anonymisation"
    _requested: ClassVar[ContextVar[tuple[str, ...]]] = ContextVar("requested_gateway_guardrails", default=())

    @classmethod
    def requested(cls) -> tuple[str, ...]:
        return cls._requested.get()

    @classmethod
    def anonymising(cls) -> bool:
        return cls.PII_ANONYMISATION in cls.requested()

    @classmethod
    @contextmanager
    def requesting(cls, *names: str) -> Iterator[None]:
        """Add guardrails for the duration of the block; nested blocks add to the outer ones."""
        token = cls._requested.set(tuple(dict.fromkeys((*cls._requested.get(), *names))))
        try:
            yield
        finally:
            cls._requested.reset(token)

    @classmethod
    def merged_into(cls, request_kwargs: dict[str, Any], names: tuple[str, ...] | None = None) -> dict[str, Any]:
        """The request kwargs with the guardrails added to `extra_body`, keeping what else the body carries.

        `names` defaults to the guardrails requested in the current context. Merged rather than set, because a
        call may already send `extra_body` (`chat_template_kwargs` to switch reasoning off).
        """
        names = cls.requested() if names is None else names
        if not names:
            return request_kwargs
        extra_body = dict(request_kwargs.get("extra_body") or {})
        extra_body["guardrails"] = list(dict.fromkeys((*extra_body.get("guardrails", ()), *names)))
        return {**request_kwargs, "extra_body": extra_body}
