import json
import math
import re
from typing import Annotated, Any, NoReturn, Self

from jsonschema import SchemaError
from jsonschema.validators import validator_for
from pydantic import BaseModel, Field, model_validator
from referencing import Registry

from swiss_ai_hub.core.events.agent.user.response_schema_violation import ResponseSchemaViolation

_CODE_FENCE = re.compile(r"^\s*```(?:json)?\s*(?P<body>.*?)\s*```\s*$", re.DOTALL)
_REFERENCE_KEYWORDS = ("$ref", "$dynamicRef")


class ResponseSchema(BaseModel):
    """The JSON shape a caller wants the agent's answer in.

    One request whatever the caller's API calls it: the OpenAI endpoint maps both `response_format` and a forced
    function call onto it, and decides on its own how to hand the result back.
    """

    name: Annotated[
        str,
        Field(
            description="A name for the shape, as OpenAI's `json_schema.name` or a function name.",
            pattern=r"^[a-zA-Z0-9_-]{1,64}$",
        ),
    ]
    description: Annotated[str | None, Field(description="What the shape is for; the model reads it.")] = None
    json_schema: Annotated[
        dict[str, Any] | None,
        Field(description="The JSON schema the answer must match. Without one, any JSON object is accepted."),
    ] = None
    strict: Annotated[
        bool,
        Field(description="Ask the model to follow the schema exactly, as OpenAI's structured outputs `strict`."),
    ] = False

    @model_validator(mode="after")
    def _schema_is_valid(self) -> Self:
        if self.json_schema is not None:
            try:
                validator_for(self.json_schema).check_schema(self.json_schema)
            except SchemaError as invalid_schema:
                raise ValueError(f"json_schema is not a valid JSON schema: {invalid_schema.message}") from None
            if external := ResponseSchema._external_reference(self.json_schema):
                raise ValueError(f"json_schema may only reference its own definitions, not {external!r}")
        return self

    @staticmethod
    def _external_reference(schema: Any) -> str | None:
        """The first reference outside the schema itself: resolving one would fetch it from the agent worker."""
        if isinstance(schema, list):
            return next(filter(None, map(ResponseSchema._external_reference, schema)), None)
        if not isinstance(schema, dict):
            return None
        for keyword in _REFERENCE_KEYWORDS:
            reference = schema.get(keyword)
            if isinstance(reference, str) and not reference.startswith("#"):
                return reference
        return next(filter(None, map(ResponseSchema._external_reference, schema.values())), None)

    def response_format(self) -> dict[str, Any]:
        """The OpenAI `response_format` that asks a model for this shape."""
        if self.json_schema is None:
            return {"type": "json_object"}
        json_schema: dict[str, Any] = {"name": self.name, "schema": self.json_schema, "strict": self.strict}
        if self.description:
            json_schema["description"] = self.description
        return {"type": "json_schema", "json_schema": json_schema}

    def validated(self, answer: str) -> dict[str, Any]:
        """The answer parsed, once it matches the schema.

        A code fence around the JSON is tolerated: a model without structured outputs often adds one. `NaN`,
        `Infinity` and numbers too large for a float are not: Python reads them, but they are not JSON, and the answer
        is handed on to strict JSON clients.
        """
        fenced = _CODE_FENCE.match(answer)
        try:
            parsed = json.loads(
                fenced.group("body") if fenced else answer,
                parse_constant=ResponseSchema._non_finite,
                parse_float=ResponseSchema._finite_float,
            )
        except json.JSONDecodeError as not_json:
            raise ResponseSchemaViolation(f"The answer is not valid JSON: {not_json}") from None
        if not isinstance(parsed, dict):
            raise ResponseSchemaViolation("The answer must be a JSON object.")
        if self.json_schema is not None:
            validator = validator_for(self.json_schema)(self.json_schema, registry=Registry())
            errors = sorted(validator.iter_errors(parsed), key=str)
            if errors:
                raise ResponseSchemaViolation(
                    "The answer does not match the schema: "
                    + "; ".join(
                        f"{'/'.join(map(str, error.absolute_path)) or '(root)'}: {error.message}" for error in errors
                    )
                )
        return parsed

    @staticmethod
    def _non_finite(constant: str) -> NoReturn:
        raise ResponseSchemaViolation(f"The answer is not valid JSON: {constant} is not a JSON number.")

    @staticmethod
    def _finite_float(number: str) -> float:
        value = float(number)
        if math.isinf(value):
            ResponseSchema._non_finite(number)
        return value
