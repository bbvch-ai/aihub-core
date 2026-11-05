import json
import time

import pytest
from pydantic import ValidationError

from swiss_ai_hub.core.events.agent.user.response_schema import ResponseSchema
from swiss_ai_hub.core.events.agent.user.response_schema_validator import ResponseSchemaValidator
from swiss_ai_hub.core.events.agent.user.response_schema_violation import ResponseSchemaViolation
from swiss_ai_hub.core.events.agent.user.user_message_event import UserMessageEvent

INVOICE = {
    "type": "object",
    "properties": {
        "issuer": {"type": "string"},
        "total": {"type": ["number", "null"]},
        "lines": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"item": {"type": "string"}, "amount": {"type": "number"}},
                "required": ["item", "amount"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["issuer", "total", "lines"],
    "additionalProperties": False,
}


def _invoice_schema(**update) -> ResponseSchema:
    return ResponseSchema(name="invoice", json_schema=INVOICE, strict=True, **update)


def test_a_nested_answer_matching_the_schema_is_parsed():
    answer = '{"issuer": "ACME AG", "total": null, "lines": [{"item": "Bolts", "amount": 12.5}]}'

    assert _invoice_schema().validated(answer) == {
        "issuer": "ACME AG",
        "total": None,
        "lines": [{"item": "Bolts", "amount": 12.5}],
    }


def test_a_code_fence_around_the_json_is_tolerated():
    assert _invoice_schema().validated('```json\n{"issuer": "ACME AG", "total": 1, "lines": []}\n```')["total"] == 1


def test_every_violation_is_named_with_its_location():
    schema = _invoice_schema()

    with pytest.raises(ResponseSchemaViolation) as violation:
        schema.validated('{"issuer": "ACME AG", "lines": [{"item": "Bolts"}]}')

    assert "(root): 'total' is a required property" in str(violation.value)
    assert "lines/0: 'amount' is a required property" in str(violation.value)


@pytest.mark.parametrize("answer", ["The total is 12.", "[1, 2]", ""])
def test_prose_and_non_objects_are_violations(answer: str):
    schema = ResponseSchema(name="any")

    with pytest.raises(ResponseSchemaViolation):
        schema.validated(answer)


def test_without_a_schema_any_object_is_asked_for_as_an_open_object_schema():
    any_object = ResponseSchema(name="any", strict=True)

    assert any_object.response_format() == {
        "type": "json_schema",
        "json_schema": {"name": "any", "schema": {"type": "object"}, "strict": False},
    }
    assert any_object.validated('{"anything": [1]}') == {"anything": [1]}


def test_the_response_format_carries_name_description_schema_and_strictness():
    assert _invoice_schema(description="An invoice's header").response_format() == {
        "type": "json_schema",
        "json_schema": {"name": "invoice", "schema": INVOICE, "strict": True, "description": "An invoice's header"},
    }


def test_an_invalid_json_schema_is_refused():
    with pytest.raises(ValidationError, match="not a valid JSON schema"):
        ResponseSchema(name="broken", json_schema={"type": "invoice"})


def test_a_name_openai_would_reject_is_refused():
    with pytest.raises(ValidationError):
        ResponseSchema(name="an invoice")


def test_the_request_is_part_of_the_api_input_and_optional():
    assert "response_schema" in UserMessageEvent.api_input_model().model_fields
    assert UserMessageEvent.model_fields["response_schema"].default is None


@pytest.mark.parametrize(
    "reference", ["http://169.254.169.254/latest/meta-data", "https://example.com/invoice.json", "invoice.json"]
)
def test_a_schema_referencing_anything_outside_itself_is_refused(reference: str):
    with pytest.raises(ValidationError, match="may only reference its own definitions"):
        ResponseSchema(name="remote", json_schema={"type": "object", "properties": {"a": {"$ref": reference}}})


def test_references_to_the_schemas_own_definitions_are_resolved():
    local = ResponseSchema(
        name="local",
        json_schema={
            "type": "object",
            "properties": {"a": {"$ref": "#/$defs/text"}},
            "$defs": {"text": {"type": "string"}},
        },
    )

    with pytest.raises(ResponseSchemaViolation, match="a: 1 is not of type 'string'"):
        local.validated('{"a": 1}')


@pytest.mark.parametrize("answer", ['{"a": NaN}', '{"a": [Infinity]}', '{"a": {"b": -Infinity}}', '{"a": 1e309}'])
def test_numbers_json_cannot_carry_are_violations(answer: str):
    schema = ResponseSchema(name="any")

    with pytest.raises(ResponseSchemaViolation, match="not a JSON number"):
        schema.validated(answer)


BACKTRACKING_ANSWER = json.dumps({"code": "a" * 40 + "!"})


def _schema_with(properties: dict, **extra) -> ResponseSchema:
    return ResponseSchema(name="shape", json_schema={"type": "object", "properties": properties, **extra})


def test_a_pattern_that_freezes_pythons_re_is_checked_at_once():
    schema = _schema_with({"code": {"type": "string", "pattern": "^(a+)+$"}})
    started = time.monotonic()

    with pytest.raises(ResponseSchemaViolation, match="does not match"):
        schema.validated(BACKTRACKING_ANSWER)

    assert time.monotonic() - started < 1


def test_a_pattern_that_backtracks_on_any_engine_is_cut_off_within_the_budget():
    schema = _schema_with({"code": {"type": "string", "pattern": "^(a|aa)+$"}})
    started = time.monotonic()

    with pytest.raises(ResponseSchemaViolation, match="took longer"):
        schema.validated(BACKTRACKING_ANSWER)

    assert time.monotonic() - started < ResponseSchemaValidator.BUDGET_SECONDS + 1


@pytest.mark.parametrize(("code", "matches"), [("AB-12", True), ("ab-12", False)])
def test_patterns_are_still_checked(code: str, matches: bool):
    schema = _schema_with({"code": {"type": "string", "pattern": "^[A-Z]{2}-[0-9]+$"}})
    answer = json.dumps({"code": code})

    if matches:
        assert schema.validated(answer) == {"code": code}
    else:
        with pytest.raises(ResponseSchemaViolation, match="does not match"):
            schema.validated(answer)


def test_pattern_properties_and_additional_properties_are_still_checked():
    schema = _schema_with({}, patternProperties={"^x-": {"type": "integer"}}, additionalProperties=False)

    assert schema.validated('{"x-count": 3}') == {"x-count": 3}
    with pytest.raises(ResponseSchemaViolation, match="x-count"):
        schema.validated('{"x-count": "three"}')
    with pytest.raises(ResponseSchemaViolation, match="'other' unexpected"):
        schema.validated('{"other": 1}')


def test_unevaluated_properties_next_to_pattern_properties_is_refused():
    with pytest.raises(ValidationError, match="unevaluatedProperties"):
        _schema_with({}, patternProperties={"^x-": {}}, unevaluatedProperties=False)


def test_an_unclosed_fence_followed_by_spaces_is_read_at_once():
    started = time.monotonic()

    schema = ResponseSchema(name="shape")
    answer = "```json" + " " * 20_000 + '{"a": 1}'

    with pytest.raises(ResponseSchemaViolation, match="not valid JSON"):
        schema.validated(answer)

    assert time.monotonic() - started < 1


def test_a_fenced_answer_with_surrounding_whitespace_is_still_read():
    assert ResponseSchema(name="shape").validated('\n  ```json\n{"a": 1}\n```  \n') == {"a": 1}


def test_a_dialect_declared_below_the_root_is_refused():
    nested = {"$schema": "https://json-schema.org/draft/2020-12/schema", "type": "string", "pattern": "^(a+)+$"}

    with pytest.raises(ValidationError, match=r"\$schema only at its root"):
        _schema_with({"code": nested})
    assert _schema_with({}, **{"$schema": "https://json-schema.org/draft/2020-12/schema"}).json_schema is not None
