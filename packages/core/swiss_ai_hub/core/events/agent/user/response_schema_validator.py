import time
from collections.abc import Callable, Iterator
from typing import Any, ClassVar

import regex
from jsonschema import ValidationError
from jsonschema.protocols import Validator
from jsonschema.validators import extend, validator_for
from referencing import Registry

from swiss_ai_hub.core.events.agent.user.response_schema_violation import ResponseSchemaViolation

type Search = Callable[[str, str], bool]


class ResponseSchemaValidator:
    """Checks an answer against a caller's schema with every regular expression bounded in time.

    jsonschema matches `pattern`, `patternProperties` and the names `additionalProperties` weighs with Python's `re`,
    which has no timeout and holds the event loop while it backtracks. A caller writes both the schema and, through the
    prompt, the answer, so one pattern such as `^(a+)+$` froze the agent for every run. Here they run on the `regex`
    engine against one budget for the whole check, and running out of it is a violation like any other.
    """

    BUDGET_SECONDS: ClassVar[float] = 1.0
    PATTERN_KEYWORD: ClassVar[str] = "patternProperties"
    UNBOUNDED_KEYWORD: ClassVar[str] = "unevaluatedProperties"

    @staticmethod
    def errors(schema: dict[str, Any], instance: Any) -> list[ValidationError]:
        search = ResponseSchemaValidator._bounded_search(time.monotonic() + ResponseSchemaValidator.BUDGET_SECONDS)
        validator_class = extend(
            validator_for(schema),
            {
                "pattern": ResponseSchemaValidator._pattern(search),
                ResponseSchemaValidator.PATTERN_KEYWORD: ResponseSchemaValidator._pattern_properties(search),
                "additionalProperties": ResponseSchemaValidator._additional_properties(search),
            },
        )
        return sorted(validator_class(schema, registry=Registry()).iter_errors(instance), key=str)

    @staticmethod
    def uses_unbounded_patterns(schema: Any) -> bool:
        """`unevaluatedProperties` weighs `patternProperties` inside jsonschema itself, where no budget applies."""
        keywords = ResponseSchemaValidator._keywords_in(schema)
        return {ResponseSchemaValidator.UNBOUNDED_KEYWORD, ResponseSchemaValidator.PATTERN_KEYWORD} <= keywords

    @staticmethod
    def _keywords_in(schema: Any) -> set[str]:
        if isinstance(schema, list):
            return set().union(*map(ResponseSchemaValidator._keywords_in, schema))
        if not isinstance(schema, dict):
            return set()
        return set(schema).union(*map(ResponseSchemaValidator._keywords_in, schema.values()))

    @staticmethod
    def _bounded_search(deadline: float) -> Search:
        def search(pattern: str, text: str) -> bool:
            try:
                return regex.search(pattern, text, timeout=max(deadline - time.monotonic(), 0.0)) is not None
            except TimeoutError:
                raise ResponseSchemaViolation(
                    f"Checking the answer against the pattern {pattern!r} took longer than the "
                    f"{ResponseSchemaValidator.BUDGET_SECONDS} s allowed."
                ) from None

        return search

    @staticmethod
    def _pattern(search: Search) -> Callable[..., Iterator[ValidationError]]:
        def pattern(validator: Validator, expected: str, instance: Any, _schema: dict[str, Any]):
            if validator.is_type(instance, "string") and not search(expected, instance):
                yield ValidationError(f"{instance!r} does not match {expected!r}")

        return pattern

    @staticmethod
    def _pattern_properties(search: Search) -> Callable[..., Iterator[ValidationError]]:
        def pattern_properties(validator: Validator, patterns: dict[str, Any], instance: Any, _schema: dict[str, Any]):
            if not validator.is_type(instance, "object"):
                return
            for expected, subschema in patterns.items():
                for key, value in instance.items():
                    if search(expected, key):
                        yield from validator.descend(value, subschema, path=key, schema_path=expected)

        return pattern_properties

    @staticmethod
    def _additional_properties(search: Search) -> Callable[..., Iterator[ValidationError]]:
        def additional_properties(validator: Validator, allowed: Any, instance: Any, schema: dict[str, Any]):
            if not validator.is_type(instance, "object"):
                return
            named = schema.get("properties", {})
            patterns = schema.get(ResponseSchemaValidator.PATTERN_KEYWORD, {})
            extras = [
                key for key in instance if key not in named and not any(search(pattern, key) for pattern in patterns)
            ]
            if validator.is_type(allowed, "object"):
                for extra in extras:
                    yield from validator.descend(instance[extra], allowed, path=extra)
            elif not allowed and extras:
                listed = ", ".join(repr(extra) for extra in sorted(extras))
                yield ValidationError(f"Additional properties are not allowed ({listed} unexpected)")

        return additional_properties
